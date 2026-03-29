<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/special-signs.yaml` file for module **3: Special Signs** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-missing-sign -->`
- `<!-- INJECT_ACTIVITY: quiz-apostrophe-or-soft-sign -->`
- `<!-- INJECT_ACTIVITY: match-up-voiced-voiceless -->`
- `<!-- INJECT_ACTIVITY: quiz-g-vs-ge -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Does this word have a soft sign, apostrophe, or neither?
  items: 8
  type: quiz
- focus: 'Match voiced-voiceless pairs: Б↔П, Д↔Т, etc.'
  items: 8
  type: match-up
- focus: 'Add the missing Ь or apostrophe: сім_я, ден_, п_ять'
  items: 6
  type: fill-in
- focus: Choose the correct pronunciation for Г vs Ґ words
  items: 4
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
- м'який (soft) — apostrophe + soft sign
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

> **Оксана:** Це **кінь**? *(Is this a horse?)*
> **Марк:** Так, це **кінь**. *(Yes, this is a horse.)*
> **Оксана:** А що це? *(And what is this?)*
> **Марк:** Це **день**. *(This is a day.)*

When you read Ukrainian, you will often encounter a symbol that changes everything about how a word feels in your mouth. Look at the letter **Ь**. It looks like a lowercase English "b", but in Ukrainian, it has a completely different job. The **Ь** is called the soft sign, or **м'який знак**. It is a very special character because it is the only letter in the entire Ukrainian alphabet that does not produce a sound of its own. Instead, it acts purely as a phonetic modifier for the consonant that comes immediately before it. The Ukrainian linguistic system draws a strict line between hard consonants, known as **тверді приголосні**, and soft consonants, known as **м'якшені приголосні**. In the authoritative Захарійчук Grade 1 textbook on page 15, this distinction is mapped out clearly for young learners: a hard consonant is marked in phonetic models with a dash [–], while a soft consonant is marked with an equals sign [=]. The soft sign's entire purpose is to change that hard [–] into a soft [=], making the sound gentler and often changing the very meaning of the word.

Let us look at how this works at the end of words, which is an extremely common grammatical pattern. Consider the hard consonant **Н**. In a word like **стан** (condition), the tongue hits the roof of the mouth firmly. Now, add the soft sign to get the soft combination **НЬ**. The middle of your tongue presses up against the hard palate, creating a much softer, almost breathy sound. You can hear this soft ending clearly in the word **день** (day), the word **кінь** (horse), or the word **осінь** (autumn). The same process happens with the letter **Л**. Without the soft sign, it is hard and firm, but with it, it becomes **ЛЬ**. Try pronouncing **сіль** (salt) or **біль** (pain). Your tongue spreads out flat across the roof of your mouth, making the sound flow smoothly. Another common pairing is **ТЬ**, as you see in **мить** (moment) or **путь** (way), and **ЗЬ**, as in **мазь** (ointment). You can also hear it clearly in **мідь** (copper).

The soft sign does not only live at the very end of words. It frequently appears right in the middle, sitting patiently between two consonants. When you see this arrangement, the **Ь** softens the first consonant, while the second one remains completely unaffected. For example, look at the formal word for father: **батько**. The **Т** is soft, but the **К** is hard. You will also see this in the word **учитель** (teacher), where it softens the final letter, or in the middle of descriptive adjectives like **маленький** (small). Because the soft sign's only job is to modify a consonant that comes before it, there is an unbreakable rule in Ukrainian orthography: the **Ь** never, ever appears at the start of a word.

<!-- INJECT_ACTIVITY: fill-in-missing-sign -->

## Апостроф (The Apostrophe)

> **Тарас:** Це **сім'я**? *(Is this a family?)*
> **Анна:** Так, це **сім'я**. *(Yes, this is a family.)*
> **Тарас:** А де **м'ясо**? *(And where is the meat?)*
> **Анна:** **М'ясо** там. *(The meat is over there.)*

You have just seen how the soft sign blends a consonant into a soft, flowing sound. Now, meet its exact opposite: the apostrophe, or **апостроф**. In Ukrainian, the apostrophe is not used for possession or contractions like it is in English. Instead, it is a critical letter-level symbol that enforces a strict "secret separation." Its visual role is to build a wall between a consonant and a vowel, preventing them from blending together. The rules for where it appears are precise. According to the foundational rule found in the Захарійчук Grade 1 textbook on page 97, the apostrophe generally only appears after the specific labial consonants **Б**, **П**, **В**, **М**, **Ф**, and the trilled **Р**. It is placed immediately before the special vowels **Я**, **Ю**, **Є**, **Ї**. Its core job is to keep that preceding consonant absolutely hard.

To truly understand why this separation is necessary, we must listen to the difference in real speech. Look at the word **пісня** (song). Here, there is no apostrophe, so the **Н** becomes naturally soft and flows right into the vowel sound. But what happens when we want the consonant to stay firm and hard? We must use the apostrophe. Look at the word for family: **сім'я**. The apostrophe tells you to pronounce the **М** hard, stop for a microsecond, and then pronounce the following vowel as two distinct sounds: a "y" sound followed by an "a" sound. This hard-stop-vowel pattern is crucial for proper pronunciation. You can practice this clear separation with the word **м'ясо** (meat). It is also highly visible in numbers, such as **п'ять** (five) and **дев'ять** (nine). You will also see it in everyday items like a **м'яч** (ball).

This rule is not just reserved for old, traditional vocabulary. The apostrophe is incredibly active in digital and modern word formation, helping integrate global concepts into the Ukrainian phonetic system. For instance, the modern word **комп'ютер** (computer) uses the apostrophe to maintain the hard **П** before the **Ю**, matching the original English rhythm perfectly while strictly following Ukrainian phonetic rules. Similarly, the word **об'єкт** (object) relies on it for clarity. Even adjectives like **м'який** (soft) use the apostrophe to establish their fundamental rhythm.

<!-- INJECT_ACTIVITY: quiz-apostrophe-or-soft-sign -->

## Дзвінкі і глухі (Voiced and Voiceless)

> **Максим:** Це **дуб**? *(Is this an oak tree?)*
> **Олена:** Так, це **дуб**. *(Yes, this is an oak tree.)*
> **Максим:** А там що? *(And what is over there?)*
> **Олена:** Там **коза**. *(There is a goat over there.)*
> **Максим:** Ні, це **коса**! *(No, this is a braid!)*

Place your hand flat against the front of your throat. Now, say the sound of the letter **З**, mimicking a buzzing bee. You will immediately feel a strong vibration under your fingers. Now, switch to the sound of the letter **С**, imitating a snake hissing. The vibration in your throat stops completely. This physical difference is the foundation of voiced and voiceless consonants, known in Ukrainian linguistics as **дзвінкі і глухі приголосні**. Voiced sounds, the **дзвінкі**, use your vocal cords to create a ringing, humming noise that carries across a room. Voiceless sounds, the **глухі**, use only rushing air to create a whispering noise. The Ukrainian language strictly organizes these sounds into eight essential pairs. These mirror pairs are **Б**-**П**, **Д**-**Т**, **Г**-**Х**, **Ґ**-**К**, **З**-**С**, **Ж**-**Ш**, **ДЗ**-**Ц**, and **ДЖ**-**Ч**. Every time you speak, you are constantly switching between these vibrating and breathy states.

Understanding these pairs leads to a defining feature of Ukrainian phonetic identity: the absolute rule of no devoicing. In many other European languages, such as Russian or German, a voiced consonant at the very end of a word becomes lazy. It drops its voice and turns into its voiceless partner, meaning a "b" sound acts like a "p" sound. Ukrainian firmly rejects this shortcut. In Ukrainian, every letter keeps its true voice in every possible position. When you read the word **дуб** (oak tree), you must pronounce a clear, strongly vibrating **Б** at the very end. It never, ever turns into a **П**. When you read **мороз** (frost), that final **З** must buzz strongly until the word is finished. The same principle applies to **ніж** (knife), where the **Ж** remains fully voiced. This commitment to clear, strong consonant endings gives spoken Ukrainian its distinct, resonant energy.

To truly master this concept, you can train your ear with minimal pairs, where one single vibration changes the entire meaning of the vocabulary word. Contrast the vibrating **Б** in **балка** (beam) with the breathy **П** in **палка** (stick). Feel the buzzing **З** in **коза** (goat) compared to the sharp, hissing **С** in **коса** (braid). Practicing these pairs will lock the sounds into your muscle memory.

<!-- INJECT_ACTIVITY: match-up-voiced-voiceless -->

## Вимова українських звуків (Pronouncing Ukrainian Sounds)

> **Віктор:** Це **кіт**. *(This is a cat.)*
> **Юлія:** А де **кит**? *(And where is the whale?)*
> **Віктор:** **Кит** там! *(The whale is over there!)*
> **Юлія:** А це **гора**? *(And is this a mountain?)*
> **Віктор:** Так, дуже **гарно**. *(Yes, very nicely.)*

Now we must look closely at a few specific sounds that require special attention, starting with the tricky vowel **И**. This letter looks exactly like a backward English "N", but it represents a sound that simply does not exist in standard English. It is a mid-retracted vowel, produced deeper and lower in the mouth. It is absolutely distinct from the high-front vowel **І**, which sounds very much like the "ee" in the English word "see". Mixing these two vowels up will cause immediate confusion. We can see this dynamic clearly in four classic minimal pairs. If you say **кит**, you are talking about a massive whale, but **кіт** is a domestic cat. The word **дим** means smoke from a fire, while **дім** means a house. The word **лис** is a wild fox, but **ліс** is a dense forest. Finally, **бик** is a strong bull, but **бік** is a side. You can practice this sound with Anna Ohoiko's pronunciation video for the letter И.

Next is the famous phonetic battle of the G letters: **Г** versus **Ґ**. They look quite similar on the page, but they represent entirely different sounds. The standard letter **Г** is a voiced glottal fricative. It sounds like a strong, voiced exhalation of breath, similar to the "h" in the English word "ahead", but with more vibration. You hear this soft, warm sound in common words like **гарно** (nicely), **гора** (mountain), and **голова** (head). The letter **Ґ**, with its little hook on top, is the familiar hard plosive, sounding exactly like the English "g" in "good" or "gate". You use it in specific words like **ґанок** (porch) and **ґудзик** (button). The letter **Ґ** is an important historical symbol of Ukrainian linguistic identity, distinguishing the language perfectly.

Finally, we have the rolling letter **Р**. The Ukrainian **Р** is trilled or tapped swiftly against the roof of the mouth, just behind your teeth. You can practice this lively sound with words like **рука** (hand), **робота** (work), **риба** (fish), and **ранок** (morning). Do not worry if you cannot roll it perfectly right away. Clear, confident communication is always much more important than achieving a perfect, theatrical trill. Practice with Anna Ohoiko's video to find your rhythm.

<!-- INJECT_ACTIVITY: quiz-g-vs-ge -->

## Підсумок — Summary

You have learned the essential mechanics of Ukrainian phonetics. To ensure these concepts are solid, ask yourself these self-check questions. First, what is the exact job of the soft sign, the **Ь**? Its only purpose is to soften the consonant that comes right before it, acting as a phonetic modifier rather than an independent sound. Second, after which six letters does the apostrophe usually appear? According to standard orthography rules, you will see it following the labial consonants **Б**, **П**, **В**, **М**, **Ф**, and the letter **Р**. Third, name three voiced-voiceless pairs. You could name **Б**-**П**, **Д**-**Т**, or **З**-**С**. Fourth, how do you pronounce a word like **дуб** at the very end? You must pronounce it with a clear, fully vibrating, voiced **Б**, because Ukrainian completely rejects the devoicing of final consonants. Finally, what is the crucial difference between the letters **Г** and **Ґ**? The letter **Г** is a soft, voiced glottal fricative that sounds like a warm breath, while **Ґ** is a hard, sharp plosive.

By understanding these elements, you have mastered the special signs that give the Ukrainian language its unique, resonant melody. The process of consonant softening makes the spoken language gentle and flowing. At the same time, the strict use of the apostrophe and the absolute rule of non-devoicing give the language its structural clarity and rhythmic strength.

To build your confidence, use this reading list for daily practice. Read these words aloud, focusing on the specific phonetic rules they represent:
- **сім'я** (family) — practice the hard **М** stop before the vowel.
- **день** (day) — practice the soft **НЬ** ending.
- **п'ять** (five) — practice the apostrophe separation.
- **гарно** (nicely) — practice the warm, breathing **Г** sound.

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

### Pattern: phonetics-soft-hard
- **group-sort** — М'який чи твердий?: Sort consonants/words by soft vs hard pronunciation
  - Instruction: *Розподіліть*
- **quiz** — Де потрібен ь?: Choose which word needs м'який знак
- **error-correction** — Виправ помилку: Find where м'який знак or апостроф is missing/wrong

### Pattern: grammar-adjectives
- **fill-in** — Який? Яка? Яке?: Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Match nouns to correct adjective forms

### Pattern: general-vocabulary
- **match-up** — Слово → переклад: Match Ukrainian words to English translations
- **fill-in** — Вставте слово: Fill in the missing word from context
- **anagram** — Склади слово: Rearrange letters to form the target word
- **odd-one-out** — Четверте зайве: Pick the word that doesn't belong to the semantic group
- **translate** — Оберіть переклад: Choose correct translation from options


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
