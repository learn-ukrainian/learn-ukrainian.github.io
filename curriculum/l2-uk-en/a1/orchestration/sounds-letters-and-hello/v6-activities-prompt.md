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

- `<!-- INJECT_ACTIVITY: quiz -->`
- `<!-- INJECT_ACTIVITY: watch-and-repeat -->`
- `<!-- INJECT_ACTIVITY: match-up -->`
- `<!-- INJECT_ACTIVITY: letter-grid -->`
- `<!-- INJECT_ACTIVITY: fill-in -->`
- `<!-- INJECT_ACTIVITY: group-sort -->`

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

Look at the text on this page. What you are seeing right now are letters. Now, say a word out loud. What you just produced is a sound. This distinction is the absolute foundation of the Ukrainian language. There is a golden rule taught to every Ukrainian student in the fifth grade, as stated by the linguist Zabolotnyi: **«Звуки ми чуємо й вимовляємо, а букви бачимо й пишемо.»** We hear and pronounce sounds (**звуки**), but we see and write letters (**літери** or **букви**). A letter is just a costume for a sound, a visual symbol on paper. In Ukrainian, this boundary between the spoken sound and the written letter is treated as a sacred distinction from the very first day of school. You cannot truly learn the language without understanding that your mouth makes sounds, and your pen writes letters.

There is a fascinating mismatch in the Ukrainian language: we have 33 letters (**літери**), but we produce 38 sounds (**звуки**). Why are there more sounds than letters? The answer lies in how some letters behave. Certain letters, specifically **Я**, **Ю**, **Є**, and **Ї**, can carry two sounds at once [йа, йу, йе, йі] depending on where they are placed in a word. Furthermore, there is one very special letter, the **Ь** (**м’який знак** or soft sign), which is a silent ghost. It makes absolutely no sound of its own. It only exists to change the texture of the consonant that comes right before it. A Ukrainian textbook by Litvinova poses a clever challenge to fifth graders: "Can you say 'vowel letter'?" The answer is strictly no! A vowel describes the physical sound you make, not the written symbol. Sounds are vowels or consonants; letters simply represent them on the page.

Let us introduce the Ukrainian alphabet (**абетка** or **алфавіт**). There are 33 letters in total, arranged in a specific, standardized order. Each letter has its own official name, like «А», «Бе», «Ве», but what matters most are the actual sounds they make: [а], [б], [в]. Unlike English, where spelling can be chaotic and unpredictable, Ukrainian spelling is highly phonetic and remarkably consistent. What you see is almost exactly what you hear. There are no silent letters hidden inside words, and no surprise pronunciations that you have to guess. Once you learn the sound of a letter, it rarely surprises you. If you know the sounds, you can read any word you see.

<!-- INJECT_ACTIVITY: quiz -->

Just like a large family, all these different sounds have two main branches. Every sound you make in Ukrainian belongs to one of two categories: **голосні** (vowels) and **приголосні** (consonants). Understanding how these two families work is your next essential step.

## Голосні звуки (Vowel Sounds)

What exactly is a vowel? We call them **голосні** (vowels), coming from the word **голос** (voice). A first-grade textbook by Bolshakova teaches this concept beautifully through a poem: **«Голосні почуєш в пісні... Легко вимовляються, весело співаються!»** You will hear vowels in a song... they are easily pronounced and cheerfully sung! The mechanics are quite simple: when you say a vowel, the air flows freely from your lungs through your mouth with absolutely no obstruction from your lips, teeth, or tongue. You use only your voice to shape the air. If you can sing it loudly across a wide field, it is definitely a vowel.

There are exactly 6 vowel sounds in Ukrainian: [а], [о], [у], [е], [и], [і]. However, as we discussed earlier, there are 10 vowel letters used to write them down: **А**, **О**, **У**, **Е**, **И**, **І**, **Я**, **Ю**, **Є**, **Ї**. The extra four letters (**Я**, **Ю**, **Є**, **Ї**) are known as "iotated" letters — they are specialized ways to write the basic vowel sounds paired with an extra "y" sound. For now, you only need to focus on the core 6 sounds. Every single Ukrainian word must have at least one vowel sound in it.

To visualize these sounds, Ukrainian first-graders use a special notation created by Zakhariichuk. Vowel sounds are marked with a solid circle [•] in sound models. Let's practice identifying the heart of the word. In the word **мама** (mother), there are two [а] sounds: [•][•]. In the word **молоко** (milk), there are three [о] sounds: [•][•][•]. In the name **Уля** (Ulya), there is one [у]. A syllable cannot possibly exist without a vowel. The vowel is the powerful motor of the word, providing all the necessary energy and rhythm.

Watch Anna Ohoiko's pronunciation videos for each vowel letter — watch, listen, and repeat.

<!-- INJECT_ACTIVITY: watch-and-repeat -->

## Приголосні звуки (Consonant Sounds)

If vowels are pure voice, consonants are sounds of obstruction. We call them **приголосні** (consonants). Bolshakova’s poem explains: **«Приголосні деренчать і тихенько шелестять...»** Consonants rattle and quietly rustle. They are formed when your mouth creates a physical barrier to the airflow. Your lips press tightly together for [п], or your tongue taps your teeth for [т]. They are made with a combination of voice and noise, or sometimes just noise alone. You cannot sing a pure consonant without a vowel’s help — try singing [к] or [п] and you will quickly run out of breath!

In Ukrainian, we have 32 consonant sounds produced by 22 consonant letters. One of the most important concepts to grasp early on is the divide between hard (**тверді**) and soft (**м'які**) consonants. Many Ukrainian consonants have a "twin" brother — one is pronounced hard, marked with a dash [–], and the other is pronounced soft, marked with an equals sign [=]. The **Ь** (**м’який знак** or soft sign) is the crucial softening agent that turns a hard consonant into its soft twin. For example, the letter **С** can be hard [с] or soft [с’]. Mastering this hard and soft distinction is the ultimate key to developing a natural native Ukrainian accent.

There are a few special characters in the consonant family you should know immediately. The letter **Ґ** represents a hard, solid 'g' sound, which is uniquely Ukrainian and quite rare. This is contrasted with the much more common **Г**, which is a breathy 'h' sound. Another very special letter is **Щ**, which always represents two distinct sounds at once: [шч], sounding exactly like "fresh cheese" when said quickly together.

<!-- INJECT_ACTIVITY: match-up -->

<!-- INJECT_ACTIVITY: letter-grid -->

## Привіт! (Hello!)

Now that you know exactly how sounds and letters work, let's look at your very first Ukrainian conversation.

> **Оленка:** Привіт! *(Hi!)*
> **Тарас:** Привіт! Як справи? *(Hi! How are you?)*
> **Оленка:** Добре, дякую. А у тебе? *(Fine, thanks. And you?)*
> **Тарас:** Чудово! *(Great!)*
> **Оленка:** Рада тебе бачити! *(Glad to see you!)*
> **Тарас:** Радий тебе бачити! *(Glad to see you!)*

Let's look at a very important grammar alert regarding gender in greetings. Notice carefully how Olenka, a woman, says **Рада тебе бачити!** (Glad to see you!), while Taras, a man, says **Радий тебе бачити!** (Glad to see you!). This is your first encounter with grammatical gender in practice. In Ukrainian, the gender of the speaker often changes the specific endings of certain words. Also, note that **привіт** (hi) is a very casual, informal greeting. You should only use it with close friends, family members, and people your own age. Never use it in formal or professional situations. You can answer **Як справи?** (How are you?) with **Добре** (fine) or **Нормально** (okay).

Let's do a linguistic deconstruction of the word **привіт** using what we have learned. We will analyze the word sound-by-sound (**звуковий аналіз**).
First is **П** [п], which is a **приголосний** (consonant).
Next is **Р** [р], another **приголосний**.
Then comes **И** [и], a **голосний** (vowel).
After that is **В** [в], a **приголосний**.
Then we have **І** [і], another **голосний**.
Finally, we end with **Т** [т], a **приголосний**.
This single word perfectly demonstrates the balance of vowels and consonants working together to create meaning!

<!-- INJECT_ACTIVITY: fill-in -->

## Підсумок (Summary)

Let's review everything we have learned with a quick self-check Q&A recap:

- Question: **Що ми чуємо і вимовляємо?** (What do we hear and pronounce?)
  Answer: **Звуки.** (Sounds.)
- Question: **Що ми бачимо і пишемо?** (What do we see and write?)
  Answer: **Літери.** (Letters.)
- Question: **Скільки літер в абетці?** (How many letters in the alphabet?)
  Answer: 33.
- Question: **Скільки звуків?** (How many sounds?)
  Answer: 38.
- Question: **Які бувають звуки?** (What kind of sounds are there?)
  Answer: **Голосні** (6 vowels) and **приголосні** (32 consonants).
- Question: **Чи можна сказати «голосна літера»?** (Can you say "vowel letter"?)
  Answer: No, you can only say "a letter representing a vowel sound." The sound itself is the vowel!
- Question: **Як сказати "Hi"?** (How do you say "Hi"?)
  Answer: **Привіт!**

<!-- INJECT_ACTIVITY: group-sort -->

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
