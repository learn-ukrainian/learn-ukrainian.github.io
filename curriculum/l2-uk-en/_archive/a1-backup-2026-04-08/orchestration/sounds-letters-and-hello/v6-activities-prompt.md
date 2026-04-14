<!-- version: 1.0.0 | updated: 2026-03-27 -->
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

- `<!-- INJECT_ACTIVITY: letter-grid -->`
- `<!-- INJECT_ACTIVITY: watch-and-repeat -->`
- `<!-- INJECT_ACTIVITY: group-sort -->`
- `<!-- INJECT_ACTIVITY: watch-and-repeat -->`
- `<!-- INJECT_ACTIVITY: group-sort -->`
- `<!-- INJECT_ACTIVITY: fill-in -->`
- `<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->`
- `<!-- INJECT_ACTIVITY: match-false-friends -->`

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

Look at this page. What you see are letters — shapes printed in ink. Now say a word out loud. Any word. What your mouth just produced is a sound — vibrations shaped by breath, lips, and tongue. In Ukrainian, this distinction is not a footnote. It is the absolute foundation of how the language is taught. Every Ukrainian student learns a golden rule in their first year of school, from the textbook of Заболотний (Grade 5, p. 83): **Звуки ми чуємо й вимовляємо, а букви бачимо й пишемо** — "We hear and pronounce sounds, but we see and write letters." Take the word **мама** (mother). You *hear* and *say* two sounds repeating — [м] then [а], [м] then [а]. You *see* and *write* four letters: М-А-М-А. A **звук** (sound) is breath shaped by your mouth and throat. A **літера** (letter) is ink on paper. These are not the same thing.

Ukrainian has **33 літери** (letters) in its alphabet, but **38 звуків** (sounds). Why the mismatch? Two reasons. First, four letters — **Я**, **Ю**, **Є**, **Ї** — can each represent *two* sounds in certain positions. You will master how this works in M02. Second, the letter **Ь** (called **м'який знак**, the soft sign) represents *no sound at all*. It is a silent instruction — it tells you that the consonant before it should be pronounced softly, and then it disappears from the sound picture entirely. There is a famous pedagogical question from Litvinova (Grade 5, p. 130): "Чи можна говорити «голосна літера»?" — "Can you say 'vowel letter'?" The answer is no. Sounds are **голосні** (vowel) or **приголосні** (consonant). Letters only *represent* sounds. They are not sounds themselves. This distinction matters throughout all of Ukrainian phonetics.

The Ukrainian alphabet is called **абетка** (also **алфавіт**). Its 33 letters run in a fixed order from **А** to **Я**. Unlike English, Ukrainian spelling is largely phonetic — what you see on the page is almost always what you say aloud. There are no "silent e" surprises, no "gh" ambiguities, no letters pretending to be other letters. Once you know the 38 sounds and which letters represent them, you can read any Ukrainian word aloud — even before you understand its meaning. From Вашуленко (Grade 2, p. 26): "Усі тут літери живуть, їх 33 — від А до Я" — "All the letters live here, all 33 — from А to Я."

Here is the full **абетка** — your map for every module ahead. Ten of these letters represent vowel sounds (marked below). Twenty-two represent consonant sounds. One — **Ь** — represents no sound at all.

| | | | | | | | | |
|---|---|---|---|---|---|---|---|---|
| **А а** | **Б б** | **В в** | **Г г** | **Ґ ґ** | **Д д** | **Е е** | **Є є** | **Ж ж** |
| **З з** | **И и** | **І і** | **Ї ї** | **Й й** | **К к** | **Л л** | **М м** | **Н н** |
| **О о** | **П п** | **Р р** | **С с** | **Т т** | **У у** | **Ф ф** | **Х х** | **Ц ц** |
| **Ч ч** | **Ш ш** | **Щ щ** | **Ь** | **Ю ю** | **Я я** | | | |

Vowel letters: А, Е, И, І, О, У + Я, Ю, Є, Ї. Consonant letters: Б, В, Г, Ґ, Д, Ж, З, Й, К, Л, М, Н, П, Р, С, Т, Ф, Х, Ц, Ч, Ш, Щ. Special: Ь (no sound — softens the consonant before it).

<!-- INJECT_ACTIVITY: letter-grid -->

## Голосні звуки (Vowel Sounds)

Ukrainian first-graders learn vowels through a poem from Большакова (Grade 1, p. 24): "Голосні почуєш в пісні, і у темному у лісі, і коли дивуєшся, і коли милуєшся. Легко вимовляються, весело співаються!" — "You'll hear vowels in a song, and in a dark forest, when you're surprised, and when you're delighted. Easy to pronounce, fun to sing!" **Голосні** (vowel sounds) are produced when air flows freely through the mouth with nothing blocking the way. Voice alone shapes them — no lips pressing together, no tongue touching the roof of your mouth, no teeth getting in the way. Because nothing obstructs the air, you can sustain a голосний indefinitely: **А-А-А-А** across a field, **О-О-О** into an empty room. You can sing every vowel. That singability is the definition.

There are six vowel *sounds*: [а], [о], [у], [е], [и], [і]. But ten vowel *letters*: А, О, У, Е, И, І — plus Я, Ю, Є, Ї. From Кравцова (Grade 2, p. 9), the chart makes this mapping explicit: the sound [а] can be written as А or Я; [у] as У or Ю; [е] as Е or Є; [і] as І or Ї. Those extra four letters — Я, Ю, Є, Ї — are called "iotated." They can add a [й] sound before the vowel in certain positions. A full explanation waits in M02. For now, the key lesson: count the *sounds*, not the letters. Ukrainian has six голосні звуки, not ten.

Hear vowels in real words. **мАмА** — two [а] sounds. **мОлОкО** (milk) — three [о] sounds (from Большакова, p. 24). **око** (eye) — two [о] sounds. **дім** (house) — one [і] sound. **ніс** (nose) — one [і] sound. Every syllable in Ukrainian contains exactly one голосний звук. Vowels are the heartbeat of syllables. A word with three vowel sounds has three syllables. When you meet a new Ukrainian word, finding the голосні is always your first step.

<!-- INJECT_ACTIVITY: watch-and-repeat -->

<!-- INJECT_ACTIVITY: group-sort -->

## Приголосні звуки (Consonant Sounds)

Where голосні flow freely, **приголосні** (consonant sounds) are blocked. Большакова (Grade 1, p. 24) captures the contrast in another poem: "Приголосні деренчать і тихенько шелестять, голосно свистять, скриплять, і гарчать, і точуть, співати не хочуть." — "Consonants rattle and quietly rustle, whistle loudly, screech, growl, and grind — they don't want to sing!" The obstruction comes from different places: lips pressing together ([м], [б], [п]), tongue touching teeth ([с], [з], [т], [д]), or the back of the throat ([г], [х]). That obstruction creates noise — hissing [с-с-с], buzzing [з-з-з], tapping [р-р-р]. Try holding [к] or [п] for three seconds. You cannot. That unsingability is what defines a приголосний.

Ukrainian has 32 consonant *sounds* from just 22 consonant letters. The reason: many consonants come in pairs — **тверді** (hard) and **м'які** (soft). From Большакова (Grade 2, p. 42): "Приголосні звуки бувають тверді та м'які." A hard [д] and a soft [д'] are two different sounds represented by the same letter **Д**. A hard [н] and a soft [н'] — same letter **Н**, two sounds. Захарійчук (Grade 1, p. 15) marks them in sound models: [–] for hard consonants, [=] for soft consonants. This hard/soft pairing does not exist in English. It is one of the distinctly Slavic features of Ukrainian phonetics, and you will return to it in depth in M03.

Three special consonant facts to note now. First, **Ґ** — a letter unique to Ukrainian, representing a hard [ґ] sound, as in **ґанок** (porch). It looks like Г but sounds different. Second, **Щ** always represents *two* sounds together: [шч]. The word **щука** (pike, the fish) starts with [шч], not a single sound. Third, the **м'який знак** (**Ь**) represents *zero* sounds. It is a softness signal, not a sound. In the word **сіль** (salt), the Ь tells you the final [л] is soft — and then Ь vanishes from the sound picture completely.

<!-- INJECT_ACTIVITY: watch-and-repeat -->

<!-- INJECT_ACTIVITY: group-sort -->

## Привіт! (Hello!)

Time for your first real Ukrainian conversation. **Привіт!** means "Hi!" — informal, used with friends, classmates, and family. After **Привіт**, the most natural follow-up is **Як справи?** (How are you?). Three answers you will hear every day: **Добре** (fine, good), **Чудово** (great, wonderful), **Нормально** (okay, so-so). To return the question: **А у тебе?** (And you?). These five phrases form the building block of every casual encounter in Ukrainian. They are not formulas to memorize in isolation — they are the actual words Ukrainians say to each other every single day.

> **Тарас:** Привіт, Оля! *(Hi, Olya!)*
> **Оля:** Привіт, Тарасе! Як справи? *(Hi, Taras! How are you?)*
> **Тарас:** Добре, дякую. А у тебе? *(Good, thanks. And you?)*
> **Оля:** Чудово! Рада тебе бачити. *(Great! Glad to see you.)*
> **Тарас:** І я радий тебе бачити! *(And I'm glad to see you!)*

Notice something: Оля says **рада** while Тарас says **радий**. Both mean "glad," but **рада** is the feminine form and **радий** is the masculine form. Ukrainian adjectives agree with the speaker's gender — confirmed in Заболотний (Grade 5, p. 218). This is your very first glimpse of grammatical gender, a major topic from M08 onward. For now, just notice the difference and use the form that matches you.

Now, a **звуковий аналіз** (sound analysis) of **Привіт** — following the method from Большакова (Grade 1, p. 29). Letter by letter: **П** [п] — приголосний; **р** [р] — приголосний; **и** [и] — голосний; **в** [в] — приголосний; **і** [і] — голосний; **т** [т] — приголосний. Count: 2 голосні, 4 приголосні. Six letters, six sounds. This single word contains every type of sound you learned today — vowels and consonants together in one real Ukrainian greeting.

<!-- INJECT_ACTIVITY: fill-in -->

<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->

<!-- INJECT_ACTIVITY: match-false-friends -->

## Підсумок (Summary)

Test yourself with these questions — every answer comes from what you learned above.

**How many letters are in the Ukrainian alphabet?** → **33 літери**.

**How many sounds does Ukrainian have?** → **38 звуків**.

**Why are there more sounds than letters?** → Because Я, Ю, Є, Ї can represent two sounds each, and Ь represents no sound — it only softens the consonant before it.

**What are голосні звуки?** → Sounds made with free-flowing voice — [а], [о], [у], [е], [и], [і]. Air passes through the mouth without obstruction. You can sing them.

**What are приголосні звуки?** → Sounds made with obstruction — lips, tongue, or teeth create noise. You cannot sing them.

**Can you say "голосна літера"?** → **Ні!** Голосні are sounds, not letters. Letters *represent* sounds — they are not sounds themselves.

**What does Привіт mean?** → Hi! (informal greeting).

**What do you say after Як справи?** → **Добре**, **Чудово**, or **Нормально** — then **А у тебе?**

**What is the difference between рада and радий?** → **Рада** is the feminine form (a woman speaking); **радий** is the masculine form (a man speaking). Both mean "glad."

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
