<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/reading-ukrainian.yaml` file for module **2: Reading Ukrainian** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in -->`
- `<!-- INJECT_ACTIVITY: quiz -->`
- `<!-- INJECT_ACTIVITY: match-up -->`
- `<!-- INJECT_ACTIVITY: quiz -->`
- `<!-- INJECT_ACTIVITY: quiz -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Divide words into syllables: мо-ло-ко, ап-те-ка'
  items: 8
  type: fill-in
- focus: How many syllables? Count the vowels.
  items: 8
  type: quiz
- focus: 'Match iotated vowels to their sound components: Я=[й]+[а]'
  items: 4
  type: match-up
- focus: Read the word and choose its meaning
  items: 6
  type: quiz


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- університет (university) — long word practice
- бібліотека (library) — 5 syllables
- фотографія (photography) — long word with Ф
- шоколад (chocolate) — Ш + О + К combination
required:
- яблуко (apple) — Я at word start = [йа]
- молоко (milk) — 3 syllables, all simple vowels
- людина (person) — Л + Ю combination
- вулиця (street) — Ц sound practice
- столиця (capital) — Київ — столиця України
- каша (porridge) — Ш sound practice
- пісня (song) — softening by Я after consonant


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Склади (Syllables)

> **Анна:** Що це? *(What is this?)*
> **Марко:** Це аптека. *(This is a pharmacy.)*
> **Анна:** Ап-те-ка? *(Ap-te-ka?)*
> **Марко:** Так! *(Yes!)*

Before you start memorizing vocabulary or exploring grammar, you need to understand how Ukrainian words are physically built. The absolute foundation of reading Ukrainian lies in understanding syllables, or **склади** (syllables). There is a "Golden Rule" taught to every Ukrainian student in the first grade, explicitly defined in the Bolshakova reading textbook (Grade 1, page 25): a word has exactly as many syllables as it has vowels, which are called **голосні звуки** (vowel sounds). This rule is unbreakable and completely reliable. You simply count the vowels, and you instantly know the number of syllables. Let us look at some simple math to illustrate this foundational concept. The word **мама** (mother) contains two vowels, so it naturally has two syllables. The word **молоко** (milk) features three vowels, meaning it has exactly three syllables. A short word like **банк** (bank) has only one vowel, so it forms exactly one syllable. If you can quickly spot the vowels, you can always map out the structure of the word.

Now that you know how to count syllables, let us explore how they are divided. The mechanics of syllable division, known in Ukrainian linguistics as **складоподіл** (syllable division), operate on a fascinating concept called the "Open Syllable Principle" or **відкритий склад** (open syllable). In the Ukrainian language, consonants strongly prefer to jump forward and start the next syllable rather than closing out the previous one. They naturally want to leave the syllable "open," ending on a clear vowel sound. Let us compare two words to see this in action. The word **молоко** (milk) divides perfectly and cleanly into **мо-ло-ко**. But what happens when consonants bunch up, like in the word **аптека** (pharmacy)? Instead of dividing it as "ап-те-ка", the consonant cluster prefers to move forward together, giving us the division **а-пте-ка**. The consonant cluster ПТ starts the new syllable. This constant push toward vowels is exactly why spoken Ukrainian sounds so continuous, melodic, and famously open. The sound flows freely without getting blocked by heavy consonant endings.

To put this phonetic theory into immediate practice, Ukrainian children use a highly effective four-step method called **звуковий аналіз** (sound analysis), as outlined in the Bolshakova textbook on page 29. Whenever you encounter a new or intimidating word, follow these exact four steps. First, find all the vowels in the word—these serve as your phonetic anchor points. Second, mark the syllable boundaries, always remembering that consonants prefer to start the next syllable. Third, sound out each individual syllable block slowly and carefully. Finally, blend the syllables together at a natural, conversational speed. Let us practice this method together. Take the long word **університет** (university). Find the vowels, and you get **у-ні-вер-си-тет**. Try saying each block individually, then blend them. Now try **шоколад** (chocolate), which divides seamlessly into **шо-ко-лад**. Read it block by block. Finally, try a shorter word: **каша** (porridge). It smoothly divides into **ка-ша**. This is the exact method native speakers use to build their reading confidence from day one.

<!-- INJECT_ACTIVITY: fill-in -->

<!-- INJECT_ACTIVITY: quiz -->

## Голосні літери (Vowel Letters)

> **Анна:** Хто це? *(Who is this?)*
> **Марко:** Це кіт. *(This is a cat.)*
> **Анна:** Де кит? *(Where is the whale?)*
> **Марко:** Кит там. *(The whale is there.)*

Let us review the important phonetic mapping we established in the previous module. Ukrainian has exactly six vowel sounds, which are represented by ten different vowel letters. First, we will focus on the six "Simple Vowels": **А**, **О**, **У**, **Е**, **И**, and **І**. These are the "honest" letters of the Ukrainian alphabet. Unlike English vowels, which can drastically change their sound depending on the letters positioned around them, these six Ukrainian letters represent exactly one sound each, every single time. They are completely consistent and reliable. You will never have to guess how to pronounce them in a new word. When you see the letter **А**, it always makes the [а] sound. When you see **О**, it always makes the [о] sound. They are straightforward and form the stable, predictable core of the language.

Within this group of simple vowels lies the "Tricky Pair": **И** versus **І**. This is one of the most important distinctions you will learn as a beginner. Let us explain the exact phonetic difference between these two letters. The letter **І** makes an [і] sound. It is a high, tense sound, and you pronounce it with a slightly "smiling" mouth, very much like the "ee" in "see". On the other hand, the letter **И** makes an [и] sound. This sound is noticeably lower and much more "relaxed", somewhat resembling the "i" in "bit", but produced slightly further back in the mouth. It is absolutely crucial to distinguish them because swapping them will completely change the meaning of words. Consider these critical minimal pairs: **кит** (whale) versus **кіт** (cat). One single letter changes a massive marine mammal into a small house pet! Another vital example is **дим** (smoke) versus **дім** (house). Listen to Anna's pronunciation videos for each of these letters—the difference might seem subtle at first, but it changes the meaning entirely.

Now we must look at the Iotated Vowels, known as **йотовані** (iotated), Part 1: **Я**, **Ю**, and **Є**. These letters are special because they play a dual role depending entirely on where they appear in a word. At the very start of a word, or immediately after another vowel, they represent two distinct sounds combined: a [й] sound followed by their corresponding basic vowel. For example, at the beginning of the word **яблуко** (apple), the letter Я makes a sharp [й] + [а] sound. Similarly, in the word **моя** (my), the letter Я follows another vowel and makes the exact same double sound. However, when these letters appear immediately after a consonant, their behavior changes entirely. Instead of making a double sound, they soften that preceding consonant and provide a single vowel sound. For instance, in the word **пісня** (song), the Я softens the consonant Н and sounds simply like [а]. Another great example is **людина** (person), where the Ю softens the Л and provides the [у] sound.

Finally, we arrive at Iotated Vowels Part 2: the letter **Ї**. The letter Ї is truly unique and can easily be considered the absolute "King" of Ukrainian vowels. Unlike its other iotated cousins, it ALWAYS represents two sounds: [й] + [і]. It stands strong and never softens the preceding consonant. In fact, it typically only appears at the start of a word, directly after another vowel, or immediately after an apostrophe. This magnificent letter is completely unique to the Ukrainian language and stands as a proud symbol of its distinct phonetic system. You will see it in incredibly important, culturally significant words, such as **Україна** (Ukraine), **поїзд** (train), and **їжа** (food). Every single time you see the letter Ї, you can confidently pronounce its double sound without hesitation.

<!-- INJECT_ACTIVITY: match-up -->

<!-- INJECT_ACTIVITY: quiz -->

## Читання слів (Reading Words)

> **Анна:** Де університет? *(Where is the university?)*
> **Марко:** Університет тут. *(The university is here.)*
> **Анна:** Де бібліотека? *(Where is the library?)*
> **Марко:** Бібліотека там. *(The library is there.)*

To read Ukrainian words smoothly, we recommend a specific strategy: "The Lego Method." When you encounter a new word in Ukrainian text, we strongly advise you not to look at the individual letters one by one. Reading letter-by-letter is a slow and frequently frustrating approach. Instead, scan the word for its vowel "cores" and build syllables around them, just like assembling interlocking bricks. Let us demonstrate this efficient approach with the word **книга** (book). First, scan the word and locate the vowels: И and А. Second, build the syllables around these anchors to get the structure **кни-га**. Finally, blend them together naturally and read the word. By deliberately starting with the vowels and building outward, you will drastically increase your reading speed and overall comprehension.

Pattern 1: CVCV (Consonant-Vowel-Consonant-Vowel). This repeating, rhythmic pattern is the absolute foundation of Ukrainian reading fluency. It is structurally simple, alternating, and very easy to pronounce. Let us practice rhythmic reading with foundational "family" words (following the teaching approach from Kravcova Grade 2, p.32). Take a deep breath and practice reading these with a steady, even pacing: **мама** (mother), **тато** (father), **вода** (water), **рука** (hand), **хата** (house), **коза** (goat), and **нога** (leg). Notice how naturally your voice bounces from a consonant directly to a vowel. Maintaining a steady pace through these fundamental words will actively train your brain to recognize this essential structural pattern instantly.

Pattern 2: CVCCV and CVC. Once you master the alternating pattern, you will begin to encounter words with consonant clusters and closed syllables. Even when consonants bunch up together, remember that the "Golden Rule" still holds true: one vowel always equals one syllable. Let us look at words containing consonant clusters: **школа** (school), **парта** (desk), and **банда** (gang). Now, consider examples of the CVC pattern, which forms short, punchy, single-syllable words: **дім** (house), **сон** (dream), **ліс** (forest), **дуб** (oak), and **хліб** (bread). When practicing these specific CVC words, focus on the abrupt, clean stop at the end of the word. They are compact, powerful words that form the vital core of everyday Ukrainian vocabulary.

Progressive Difficulty Level 2: 3-syllable words. Now it is time to push forward and move beyond basic two-syllable chunks. As words get longer, your goal is to maintain that smooth "Open Syllable" flow without hesitating or stumbling. Do not pause too long between the syllables; let them glide cleanly into one another. Practice reading these essential three-syllable words out loud: **аптека** (pharmacy), **молоко** (milk), **людина** (person), **вулиця** (street), and **столиця** (capital). You will also see this in important phrases like **Київ — столиця України** (Kyiv is the capital of Ukraine). As you read them, keep your eyes constantly moving forward to the next vowel core.

Progressive Difficulty Level 3: 4+ syllables and City Names. You are now fully ready for high-value, multi-syllable vocabulary. While these words may look intimidatingly long, the underlying strategy remains exactly the same. Break them down meticulously around their vowels. Practice these longer words: **університет** (university), **бібліотека** (library), and **фотографія** (photography). A fantastic and highly practical way to practice reading is by exploring major Ukrainian city names. Take your time and carefully sound out these beautiful cities: **Київ** (Kyiv), **Львів** (Lviv), **Одеса** (Odesa), **Харків** (Kharkiv), **Дніпро** (Dnipro), and **Полтава** (Poltava). Each city gives you an excellent opportunity to practice your syllable blending.

Special signs preview. Before we conclude this reading module, let us briefly introduce three special visual markers that will alter how you read certain words. These concepts will be explored deeply in the next module, but you should recognize them now. First, the letter **Щ** is unique because it always represents a double sound, [ш] + [ч]. You can see it in common words like **що** (what) and **ще** (more). Second, the **Ь** (soft sign) is completely silent, but it fundamentally changes the preceding consonant, making it soft. Look at the words **день** (day) and **сіль** (salt). Finally, the Apostrophe forces a hard break or separation between sounds, directly preventing them from blending together. You will see this specific marker in words like **сім’я** (family) and **м’ясо** (meat).

<!-- INJECT_ACTIVITY: quiz -->

## Підсумок — Summary

You have now learned the most powerful tools for reading Ukrainian. Remember that the absolute key to unlocking any new word is applying the syllable rule, perfectly balanced with a deep understanding of the ten vowel letters. Use this simple self-check list to verify your phonetic progress:

* How do you count syllables in a Ukrainian word? (Count the vowels!)
* What are the sіx basic vowel sounds? ([а], [о], [у], [е], [и], [і])
* Name the four iotated vowel letters. (Я, Ю, Є, Ї)
* What does the letter Ь do? (It softens the preceding consonant and has no sound of its own)
* What does the apostrophe do? (It forces a hard separation between sounds)
* Challenge: How many syllables are in the word **бібліотека** (library)? (There are 5 syllables, because there are 5 vowels!)

Keep practicing these fundamental reading patterns, and very soon, decoding Ukrainian text will feel completely natural and rhythmic.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: reading-ukrainian
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

**Level: A1.1 (Module 2/55) — COMPLETE BEGINNER**

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

### Pattern: phonetics-syllables
- **divide-words** — Поділи слова на склади: Interactive syllable division — tap between letters to insert hyphens
  - Instruction: *Поділіть слово на склади*
- **count-syllables** — Порахуй склади: Count syllables — each vowel = one syllable (складотворчі голосні)
  - Instruction: *How many syllables?*
- **pick-syllables** — Вибери закриті/відкриті склади: Classify syllables as відкритий (ends vowel) or закритий (ends consonant)
  - Instruction: *Select all closed syllables (закриті склади)*
- **odd-one-out** — Четверте зайве: Pick the word that doesn't belong — by syllable count, type, or pattern
  - Instruction: *Яке слово зайве?*

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
