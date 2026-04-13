<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/free-time.yaml` file for module **26: Free Time** (a1).

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

- `<!-- INJECT_ACTIVITY: match-hobbies-verbs -->`
- `<!-- INJECT_ACTIVITY: fill-in-prepositions-activities -->`
- `<!-- INJECT_ACTIVITY: fill-in-invitations-frequency -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Match the verb to the logical noun (hobbies)
  pairs:
  - грати ↔ у футбол
  - грати ↔ на гітарі
  - слухати ↔ музику
  - дивитися ↔ фільми
  - ходити ↔ в кіно
  - ходити ↔ в театр
  - читати ↔ книгу
  - малювати ↔ вдома
  type: match-up
- focus: Complete the invitations and frequency sentences
  items:
  - Я {ніколи не|завжди|часто} працюю у неділю.
  - Вона грає у теніс двічі {на тиждень|у тиждень|в тиждень}.
  - — {Ходімо|Давай|Ідемо} в кіно у суботу! — Добре!
  - Я люблю спорт, тому {часто|ніколи|рідко} граю у баскетбол.
  - Я не маю часу, тому {рідко|часто|завжди} читаю книги.
  - — Що ти робиш {у вихідні|вихідні|на вихідні}? — Відпочиваю.
  type: fill-in
- focus: Choose the correct preposition for the activity
  items:
  - Він грає {на|у|в} піаніно.
  - Ми граємо {у|на|в} футбол.
  - Я хочу ходити {на|в|у} концерт.
  - Вони ходять {в|на|у} театр раз на місяць.
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- завжди (always)
- зазвичай (usually)
- ніколи (never)
- театр (theater, m)
- концерт (concert, m)
- музей (museum, m)
- давай (let's — informal)
- раз (once/time)
required:
- вихідні (weekend, pl)
- спорт (sport, m)
- футбол (football, m)
- кіно (cinema, n — indeclinable)
- часто (often)
- іноді (sometimes)
- рідко (rarely)
- ходімо (let's go!)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

Community centers and public bulletin boards are common places to find out about local events, clubs, and activities in Ukraine. Imagine **Вітя** (Vitya) and **Оленка** (Olenka) standing in front of a colorful bulletin board at their local cultural center. They are reading posters about upcoming concerts, sports teams, and art classes. This is the perfect moment for them to talk about what they do for fun and make plans. In Ukrainian, when we want to ask someone about their hobbies or weekend plans, we use specific conversational patterns. Let's listen to how Вітя and Оленка discuss their free time.

> **Вітя:** Привіт, Оленко! Що ти робиш у **вихідні**? *(Hi, Olenka! What do you do on the weekend?)*
> **Оленка:** Привіт! **Зазвичай** я гуляю і читаю. *(Hi! Usually I walk and read.)*
> **Вітя:** **Ходімо** в **кіно** в суботу! *(Let's go to the cinema on Saturday!)*
> **Оленка:** Добре! О котрій? *(Good! At what time?)*
> **Вітя:** О п'ятій. *(At five.)*
> **Оленка:** Чудово! *(Great!)*

Notice how Вітя asks «Що ти робиш у вихідні?» (What do you do on the weekend?). The word **вихідні** (weekend) is always plural in Ukrainian. Olenka replies with «Зазвичай я гуляю і читаю» (Usually I walk and read), using the adverb **зазвичай** (usually) to describe her habit. When Вітя wants to invite her out, he uses the powerful invitation word **ходімо** (let's go!). He says «Ходімо в кіно в суботу!» (Let's go to the cinema on Saturday!). This pattern is very natural: you state the invitation, the place, and then the day. Finally, they confirm the time using the question «О котрій?» (At what time?) and the answer «О п'ятій» (At five).

> **Оленка:** Вітю, ти любиш **спорт**? *(Vitya, do you like sport?)*
> **Вітя:** Так, я граю у **футбол**. *(Yes, I play football.)*
> **Оленка:** Як **часто**? *(How often?)*
> **Вітя:** Двічі на тиждень, у вівторок і четвер. *(Twice a week, on Tuesday and Thursday.)*
> **Оленка:** А ще? *(And what else?)*
> **Вітя:** **Іноді** слухаю музику і малюю. *(Sometimes I listen to music and draw.)*

In this second conversation, Olenka asks a direct question: «Ти любиш спорт?» (Do you like sport?). The word **спорт** (sport) is easy to recognize. Vitya answers affirmatively with «Так, я граю у футбол» (Yes, I play football), using the word **футбол** (football). Olenka wants to know more about his routine, so she asks «Як часто?» (How often?). The word **часто** means "often". Vitya gives a precise answer: «Двічі на тиждень» (Twice a week). He also adds more details about his other interests, saying «Іноді слухаю музику» (Sometimes I listen to music). The word **іноді** (sometimes) shows that this is an occasional hobby.

:::note
In Ukraine, many towns and cities have a «Будинок культури» (House of Culture). These are active community centers where people of all ages go to participate in art classes, sports, dance groups, and musical performances. Bulletin boards in these centers are great places to find a new hobby or join a club!
:::

## Хобі і спорт (Hobbies and Sports)

To start a conversation about hobbies, you can ask a very direct and polite question: «Що ти любиш робити у вільний час?» (What do you like to do in your free time?). We already know the verb «любити» (to love, to like). When we want to talk about our hobbies, we simply use «Я люблю» (I like) followed by the dictionary form (infinitive) of an action verb. For example, if your hobby is reading, you say «Я люблю читати» (I like to read). If you enjoy relaxing, you can say «Я люблю відпочивати» (I like to rest). This structure expands on what we learned previously and is the easiest way to express your interests.

When we talk about playing sports or games, Ukrainian uses a very specific pattern. We take the verb «грати» (to play), add the preposition «у» or «в» (in/at), and then name the sport. Unlike English, which just says "play football", Ukrainian requires this preposition. It literally translates to "play in football".

*   **Я граю у футбол.** (I play football.)
*   **Він грає у баскетбол.** (He plays basketball.)
*   **Ми граємо у теніс.** (We play tennis.)

:::tip
How do you know whether to use «у» or «в»? Ukrainian loves harmony and flow! If the previous word ends in a consonant and the next word starts with a consonant, we use «у» to break them up to make pronunciation easier. If there are vowels around, we prefer «в». This rule is called euphony, or "beautiful sounding."
:::

However, if your hobby is playing a musical instrument, the pattern changes completely! Instead of the preposition «у» or «в», Ukrainian uses the preposition «на» (on) for instruments. You are literally saying that you "play on" the guitar or piano. This is a strict rule in Ukrainian. We play «у» sports, but we play «на» instruments. Think of your hands resting on the instrument to make music.

*   **Я граю на гітарі.** (I play the guitar.)
*   **Вона грає на піаніно.** (She plays the piano.)
*   **Ти граєш на скрипці?** (Do you play the violin?)

Of course, not everyone plays sports or instruments. There are many other relaxing activities you can describe using simple verbs. You can combine these action verbs with nouns to create full hobby phrases without needing any extra prepositions.

*   **Я люблю слухати музику.** (I like to listen to music.)
*   **Ми любимо дивитися фільми.** (We like to watch movies.)
*   **Вони люблять дивитися серіали.** (They like to watch series.)
*   **Я малюю.** (I draw.)
*   **Він фотографує.** (He takes photos.)

Notice how we use the verb «слухати» (to listen) directly with «музику» (music), or «дивитися» (to watch) directly with «фільми» (movies) or «серіали» (series).

Another very important verb for free time is «ходити» (to go regularly). We use this verb to talk about places we visit for entertainment as a habit. For now, you should learn these phrases as fixed vocabulary chunks. The grammar behind these endings will be explained later.

*   **Я ходжу в кіно.** (I go to the cinema.)
*   **Він ходить у театр.** (He goes to the theater.)
*   **Ми ходимо на концерт.** (We go to a concert.)
*   **Вони ходять у музей.** (They go to a museum.)

The words **театр** (theater), **концерт** (concert), and **музей** (museum) are very useful for making weekend plans. The word **кіно** (cinema) is special because it never changes its ending, no matter how we use it in a sentence!

<!-- INJECT_ACTIVITY: match-hobbies-verbs -->

<!-- INJECT_ACTIVITY: fill-in-prepositions-activities -->

## Як часто? (How Often?)

Once you know someone's hobbies, the next logical question is to ask about their routine. You can ask «Як часто?» (How often?). To answer this, we need a special group of words called frequency adverbs. These words tell us how regularly an action happens.

*   **завжди** (always)
*   **зазвичай** (usually)
*   **часто** (often)
*   **іноді** / **інколи** (sometimes)
*   **рідко** (rarely)
*   **ніколи** (never)

The words **іноді** and «інколи» mean exactly the same thing. You can use whichever one you prefer. These adverbs are incredibly useful because they allow you to add detail and precision to your daily routine descriptions.

In a Ukrainian sentence, frequency adverbs are almost always placed directly before the main verb. They describe the action, so they sit right next to it. 

*   **Я часто гуляю.** (I often walk.)
*   **Я іноді читаю.** (I sometimes read.)
*   **Він зазвичай працює.** (He usually works.)

There is one extremely important rule when using the word **ніколи** (never). Ukrainian requires a double negation. This means that if you use the word "never", you must also add the negative particle «не» (not) before the verb.

*   **Я ніколи не працюю у неділю.** (I never work on Sunday.)
*   **Ми ніколи не дивимося серіали.** (We never watch series.)

:::caution
English speakers often make a mistake with the word **ніколи** (never). In English, we say "I never work", using only one negative word. In Ukrainian, you must use a double negative! You have to say "I never *do not* work" («Я ніколи не працюю»). If you forget the «не», the sentence will sound completely broken to a native speaker.
:::

Sometimes adverbs like "often" or **рідко** (rarely) are not specific enough. When you want to give an exact schedule, you can use numbers combined with the word **раз** (once / one time). The word **раз** is used to count occurrences.

*   **раз на тиждень** (once a week)
*   **двічі на тиждень** (twice a week)
*   **тричі на тиждень** (three times a week)
*   **кожен день** (every day)

You can place these specific frequency expressions at the end of your sentence to give clear details about your routine.

*   **Я граю у футбол двічі на тиждень.** (I play football twice a week.)
*   **Я ходжу в кіно раз на місяць.** (I go to the cinema once a month.)

Now that you can talk about your hobbies and schedule, you might want to invite someone to join you! The most natural and authentic Ukrainian way to say "Let's go!" is **ходімо!**. This is a powerful, enthusiastic invitation that you can combine with activities, days, and times.

*   **Ходімо в кіно у суботу!** (Let's go to the cinema on Saturday!)
*   **Ходімо в парк!** (Let's go to the park!)

If you are speaking casually with a good friend, you can also use the informal word **давай!** (let's!).

*   **Давай грати у теніс!** (Let's play tennis!)
*   **Давай дивитися фільм!** (Let's watch a movie!)

<!-- INJECT_ACTIVITY: fill-in-invitations-frequency -->

## Підсумок — Summary

In this module, we expanded our ability to communicate about free time and entertainment. You learned how to state your hobbies clearly using the pattern «Я люблю» followed by an infinitive action verb. We also discovered that Ukrainian uses very specific prepositions for playing. Remember the rule: you use «у» or «в» for sports («Я граю у футбол», «Я граю в баскетбол»), but you must use «на» for musical instruments («Я граю на гітарі», «Я граю на піаніно»). Knowing this difference makes your Ukrainian sound much more natural and authentic.

We also practiced how to make exciting weekend plans. To invite a friend out, the best word to use is **ходімо!** (let's go!). This single word is a complete invitation. You can combine it with places we like to visit, such as the cinema or the theater. For example, you can say «Ходімо в кіно!» or «Ходімо на концерт!». If you are talking to a close friend in a relaxed setting, you can also use the casual word **давай!** to suggest an activity.

To add detail to your conversations, you now have a full set of vocabulary for expressing frequency. You can answer the question «Як часто?» (How often?) using general adverbs like **завжди** (always), **часто** (often), **іноді** (sometimes), **рідко** (rarely), and **ніколи** (never). Just remember the double negation rule: **ніколи** must be paired with «не». If you need to be precise, you can use numbered expressions like «раз на тиждень» (once a week) or «двічі на тиждень» (twice a week).

:::tip
The best way to remember these frequency words is to connect them to your actual life. Pick your favorite hobby and write down your schedule. Seeing your own routine written in Ukrainian will help lock these words into your memory!
:::

Now it is time to practice these new skills yourself. Try to complete this quick self-check to see how much you have remembered:

*   Name 3 hobbies you have in Ukrainian using the «Я люблю» pattern.
*   Look at your hobbies. How often do you do each one? Try to use a different frequency word for each.
*   Think of a friend. Invite them to do something fun this weekend using the phrase **ходімо**.
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: free-time
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

**Level: A1.4+ (Module 26/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-verbs-present [§4.2.4.1]
**Дієвідмінювання в теперішньому часі** (Present tense conjugation)
- **fill-in** — Відмінюй дієслово: Вставити правильну форму дієслова за особою та числом / Fill in correct verb conjugation for given person/number
  - Instruction: *Вставте правильну форму дієслова*
- **group-sort** — І чи ІІ дієвідміна?: Розподілити дієслова за типом дієвідміни / Sort verbs by conjugation class (I vs II)
- **match-up** — Особа → форма: Зіставити особові займенники з формами дієслова / Match personal pronouns to verb conjugation forms
  - Instruction: *З'єднайте*
- **error-correction** — Виправ дієслово: Знайти неправильно відмінене дієслово та виправити / Find incorrectly conjugated verb and fix it
**Anti-patterns (DO NOT generate):**
- ❌ translate: Переклад не тестує відмінювання. Англійські дієслова не змінюються за особами

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

### Pattern: grammar-pluralization [§4.2.1.1]
**Множина іменників** (Noun plurals)
- **fill-in** — Утвори множину: Утворити множину іменника — закінчення -и vs -і залежно від приголосного / Form noun plural — -и vs -і endings depending on consonant
  - Instruction: *Напишіть множину*
- **group-sort** — Закінчення -и чи -і?: Розподілити іменники за типом закінчення множини / Sort nouns by plural ending type
  - Instruction: *Розподіліть*
- **match-up** — Однина → множина: Зіставити форму однини з формою множини / Match singular form to plural form
  - Instruction: *З'єднайте*
- **error-correction** — Виправ множину: Знайти неправильну форму множини та виправити / Find incorrect plural form and fix it
**Anti-patterns (DO NOT generate):**
- ❌ quiz-only: Множина — це словотворення. Учні мають продукувати форми, а не тільки вибирати
- ❌ fill-in-no-options: На A1 завжди давати варіанти — учень ще не знає всіх закінчень

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
