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

- `<!-- INJECT_ACTIVITY: quiz-reading-practice -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Distinguish between sounds (звуки) and letters (літери). Example questions:
    ''Що ми чуємо і вимовляємо?'' → ''звуки'' | ''Що ми бачимо і пишемо?'' → ''літери''
    | ''Скільки літер в абетці?'' → ''33'' | ''Скільки звуків в українській мові?''
    → ''38''.'
  items: 6
  type: quiz
- focus: 'Match false friend Cyrillic letters to their REAL sounds. Pairs: В ↔ [в]
    (not ''b''), Н ↔ [н] (not ''h''), Р ↔ [р] (not ''p''), С ↔ [с] (not ''c/k''),
    У ↔ [у] (not ''y''), Х ↔ [х] (not ''x'').'
  items: 6
  type: match-up
- focus: 'Complete a basic greeting dialogue with blanks. EXACT pattern: ''— {Привіт}!
    Як {справи}?'' / ''— {Добре}. А у {тебе}?'' / ''— {Чудово}.'' Options per blank:
    Привіт / справи / Добре / тебе / Чудово / Нормально.'
  items: 4
  type: fill-in
- focus: 'Sort Cyrillic letters into Голосні (vowels) and Приголосні (consonants).
    Голосні: А, О, У, Е, И, І. Приголосні: К, М, Т, В, Н, Р, С, Х.'
  items: 8
  type: group-sort


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- банк (bank)
- аптека (pharmacy)
- метро (metro)
- пошта (post office)
- зупинка (bus stop)
- нормально (okay)
required:
- мама (mother)
- тато (father)
- вода (water)
- рука (hand)
- книга (book)
- школа (school)
- привіт (hi, informal)
- як справи (how are you)
- добре (fine, good)
- чудово (great, wonderful)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Звуки і літери (Sounds and Letters)

Look at the text on this page. What you are seeing right now are letters. Now, say a word out loud. What you just produced is a sound. This distinction is the absolute foundation of the Ukrainian language. There is a golden rule taught to every Ukrainian student in the first grade: **Ми чуємо і вимовляємо звуки, а бачимо і пишемо літери** (We hear and pronounce sounds, but we see and write letters). In Ukrainian, there are exactly 33 **літери** (letters) in the alphabet, but there are 38 **звуки** (sounds) that we can pronounce. The letters are simply the physical symbols we write on paper or type on a screen, while the sounds are what we actually hear and speak. 

The first family of sounds is called **голосні** (vowels). These sounds are made using your voice only. When you say them, your mouth is open, and the air flows freely with no obstruction from your lips or tongue. A popular Ukrainian textbook poem by Bolshakova teaches this concept to children: "Голосні почуєш в пісні" (You will hear vowels in a song). There are only 6 vowel sounds in the entire language: [а], [о], [у], [е], [и], and [і]. However, we use 10 vowel letters to write these sounds down on paper: **А**, **О**, **У**, **Е**, **И**, **І**, **Я**, **Ю**, **Є**, and **Ї**. 

The second family of sounds is called **приголосні** (consonants). Unlike vowels, these sounds are made with voice plus noise, or sometimes with noise only. When you pronounce a consonant, your lips, teeth, and tongue work together to create an obstruction in your mouth. There are 32 consonant sounds in total. As the same textbook poem beautifully explains: "Приголосні деренчать, і тихенько шелестять" (Consonants rattle, and quietly rustle).

:::quiz
title: "Звук чи літера?"
---
- q: "Що ми чуємо і вимовляємо?"
  o: ["звуки", "літери", "слова"]
  a: 0
- q: "Що ми бачимо і пишемо?"
  o: ["літери", "звуки", "речення"]
  a: 0
- q: "Скільки літер в абетці?"
  o: ["33", "38", "10"]
  a: 0
- q: "Скільки звуків в українській мові?"
  o: ["38", "33", "32"]
  a: 0
- q: "Які звуки утворюються тільки голосом?"
  o: ["голосні", "приголосні"]
  a: 0
- q: "Які звуки створюють перешкоду в роті?"
  o: ["приголосні", "голосні"]
  a: 0
:::

## Перші слова (First Words)

Many Cyrillic letters look exactly like Latin letters and sound almost identical to what an English speaker expects. These friendly letters are **А**, **О**, **К**, **М**, and **Т**. Because they are so familiar, you can start reading real Ukrainian words immediately. Look at the word **мама** (mother). You already know how to read it. Now look at **тато** (father), **кома** (comma), **атом** (atom), **мак** (poppy), and **око** (eye). One important detail: the Ukrainian **Т** is dental, meaning your tongue touches your upper teeth, not the gum ridge above them. Also, the letters **К** and **Т** are unaspirated, meaning there is no puff of air when you say them. 

The biggest trap for English speakers is a group of letters we call the "False Friends." These letters look like English letters, but they produce completely different sounds. The letter **В** sounds like [в] (not "b"). The letter **Н** sounds like [н] (not "h"). The letter **Р** sounds like a rolled [р] (not "p"). The letter **С** sounds like [с] (not "c" or "k"). The letter **У** sounds like [у] (not "y"). The letter **Х** sounds like a breathy [х] (not "x"). You can practice these tricky letters with these words: **вода** (water), **рука** (hand), **сон** (dream), **ніс** (nose), and **хата** (house). 

:::match-up
title: "Match false friend Cyrillic letters to their REAL sounds"
---
- left: "В"
  right: "sounds like [в], not 'b'"
- left: "Н"
  right: "sounds like [н], not 'h'"
- left: "Р"
  right: "sounds like [р], not 'p'"
- left: "С"
  right: "sounds like [с], not 'c/k'"
- left: "У"
  right: "sounds like [у], not 'y'"
- left: "Х"
  right: "sounds like [х], not 'x'"
:::

Next, you will encounter completely new shapes that have no direct Latin equivalent. These include **Б**, **Г**, **Ґ**, **Д**, **Ж**, **З**, **И**, **Й**, **Л**, **П**, **Ф**, **Ц**, **Ч**, **Ш**, and **Щ**. You can recognize them easily in words like **банк** (bank), **дім** (house), **зима** (winter), **книга** (book), and **школа** (school). Note that the letter **Щ** always makes two sounds together: [шч]. Additionally, the soft sign **Ь** has no sound of its own at all; it merely softens the consonant that comes directly before it.

Finally, there are some special letters to recognize. The letter **Ї** is unique to the Ukrainian language. It always equals two sounds [йі] and it never softens the letter before it. The letters **Я**, **Ю**, and **Є** can either represent two sounds or soften a preceding consonant. This will be fully explored in the next module, but for now, just try to recognize their shapes.

:::group-sort
title: "Sort Cyrillic letters into Голосні (vowels) and Приголосні (consonants)"
---
groups:
  - name: "Голосні"
    items: ["А", "О", "У", "Е", "И", "І"]
  - name: "Приголосні"
    items: ["К", "М", "Т", "В", "Н", "Р", "С", "Х"]
:::

## Привіт! (Hello!)

Let us look at your very first Ukrainian conversation. The most common informal greeting is **Привіт!** (Hi!). You will use this word constantly with your friends, family members, and peers. Right after greeting someone, you can ask **Як справи?** (How are you?). There are several great ways to answer this question. You can say **Добре** (good), you can say **Чудово** (great), or you can simply say **Нормально** (okay). To be polite and keep the conversation going, you can return the question by asking **А у тебе?** (And you?).

> **Оленка:** Привіт! Як справи? *(Hi! How are you?)*
> **Тарас:** Добре! А у тебе? *(Good! And you?)*
> **Оленка:** Чудово! *(Great!)*

Another wonderful phrase to learn right away is "Glad to see you!". In Ukrainian, this phrase changes depending on who is speaking. A female speaker says **Рада тебе бачити!** (Glad to see you!). A male speaker says **Радий тебе бачити!** (Glad to see you!). This is your first encounter with gender in the Ukrainian language. Words often change their endings based on whether they describe a masculine or feminine concept. This is a very important pattern that will become a major topic starting in module eight. 

Let us use the word **Привіт!** as a reading practice exercise. We can sound out each letter and identify which group it belongs to. The letter **П** is a new shape. The letter **р** is a false friend. The letter **и** is a new vowel. The letter **в** is another false friend. The letter **і** is a familiar vowel, and the letter **т** is a familiar consonant. When you blend them all together into syllables, you get: При-віт!

:::fill-in
title: "Complete a basic greeting dialogue with blanks"
---
- sentence: "— ___! Як справи?"
  answer: "Привіт"
- sentence: "— Привіт! Як ___?"
  answer: "справи"
- sentence: "— Добре. А у ___?"
  answer: "тебе"
- sentence: "— ___."
  answer: "Чудово"
:::

## Читаємо (Reading Practice)

One of the best ways to practice reading Cyrillic is through environmental reading. Imagine walking down a street in Ukraine and looking at the common signs around you. You will see **Аптека** (pharmacy), **Банк** (bank), and **Кафе** (cafe). Further down the street, you might spot the **Метро** (metro), a **Пошта** (post office), a **Школа** (school), or a **Зупинка** (bus stop). Guide your eyes through each word slowly. Sound out each letter one by one, blend them together into syllables, and then read the entire word out loud. 

You can also practice your reading skills by looking at major Ukrainian city names. Try reading **Київ** (Kyiv), **Львів** (Lviv), **Одеса** (Odesa), **Харків** (Kharkiv), **Дніпро** (Dnipro), and **Полтава** (Poltava). Notice how the letters work together. Encourage yourself to recognize both the familiar letters that look like English and the entirely new shapes. By sounding out these famous locations, you are training your brain to decode the Cyrillic alphabet quickly and accurately. 

Now you can form your very first actual sentences using the word **Це** (this is). Look at these simple sentences: **Це мама** (This is mother). **Це банк** (This is a bank). **Це Київ** (This is Kyiv). To ask questions about what you are seeing, you only need two basic question words. If you are asking about an object, you say **Що це?** (What is this?). If you are asking about a person, you say **Хто це?** (Who is this?). 

<!-- INJECT_ACTIVITY: quiz-reading-practice -->

## Підсумок — Summary

You have learned the fundamental difference between sounds and letters: there are 33 **літери** (letters) that we write, but 38 **звуки** (sounds) that we hear and pronounce. You now recognize the two main sound families: **голосні** (vowels) which use only your voice, and **приголосні** (consonants) which use your voice and noise. Always remember to watch out for the false friend letters (В, Н, Р, С, У, Х) that look like English but sound completely different in Ukrainian. You also learned essential conversational phrases like **Привіт!** (Hi!), **Як справи?** (How are you?), and how to answer with **Добре** (good) or **Чудово** (great). Finally, you practiced your reading skills by decoding common street signs and major city names. Keep practicing these signs and sounding out new Cyrillic words to build your reading speed before moving on to the next module.

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

## Quality Rules

1. **Instructions in Ukrainian** — all `instruction` fields must be in Ukrainian (the learner is learning Ukrainian)
2. **3-5 options per quiz/fill-in** — enough to prevent guessing, not so many to overwhelm
3. **No duplicate options** — each option in a quiz item must be unique
4. **Answer must be in options** — for quiz items, `correct` must be a valid index. For fill-in with options, `answer` must appear in `options`.
5. **Plausible distractors** — wrong options should be real Ukrainian words that test the specific skill. Not random words.
6. **Min 3 pairs for match-up** — to prevent trivial elimination
7. **Explanations for true-false and error-correction** — help the learner understand WHY
8. **Test LANGUAGE, not trivia** — exercises must test Ukrainian language skills. Not "In what year..." factual recall.

---

## Verification Tools (MCP)

Use these tools to verify your exercise content:



---

## Live Verification Tools (MCP)

You have access to RAG-powered MCP tools to verify Ukrainian language constructs **live as you write**. The research phase is already complete; use these tools strictly for targeted verification to ensure zero Russianisms, accurate grammar, and authentic usage.

**Core Tools:**
- `rag_verify_words` / `rag_verify_word` / `rag_verify_lemma` — VESUM morphological dictionary (409K lemmas, 6.7M forms). Returns full declension/conjugation.
- `rag_search_text` — Ukrainian school textbooks (Grades 1-11, 23K chunks).
- `rag_search_literary` — Primary literary sources (chronicles, poetry, legal texts).
- `rag_query_pravopys` — Official Ukrainian orthography rules (Правопис 2019).
- `rag_query_wikipedia` — Ukrainian Wikipedia.

**Dictionary Tools (NEW — use these for quality):**
- `rag_search_style_guide` — **Антоненко-Давидович (279 entries). HIGH PRIORITY.** Identifies calques and Russianisms. Use when unsure if a phrase is natural Ukrainian.
- `rag_query_cefr_level` — PULS CEFR vocabulary (5.9K words). Check if a word is level-appropriate (A1/A2/B1 etc.).
- `rag_search_definitions` — СУМ-11 (127K entries). Look up exact Ukrainian definitions.
- `rag_search_etymology` — Грінченко (67K entries). Historical forms, etymology.
- `rag_search_idioms` — Фразеологічний (25K entries). Find natural Ukrainian idioms.
- `rag_search_synonyms` — Ukrajinet WordNet (122K synsets). Synonyms, antonyms.
- `rag_translate_en_uk` — Балла EN→UK (79K entries). English→Ukrainian translations.
- `rag_query_grac` — GRAC corpus (2B tokens). Check word frequency, collocations, concordance. Use when unsure if a collocation is natural.
- `rag_query_ulif` — ULIF morphological paradigms. Full declension/conjugation tables. Use when verify_lemma isn't enough.
- `rag_query_r2u` — Russian→Ukrainian equivalents. Use when you suspect a word might be a Russicism — finds the proper Ukrainian alternative.

**WHEN to use tools (Specific Triggers):**

1. **Suspected Russianisms or Surzhyk (HIGH PRIORITY):**
   - *Trigger:* You are about to use a word that sounds similar to Russian, a calque, or you are unsure of its exact Ukrainian equivalent.
   - *Action:* Use `rag_search_style_guide` first (it knows calques). Then `rag_query_r2u` for the proper Ukrainian equivalent. Then verify with `rag_verify_words`.
   - *Example:* Checking *приймати участь* (calque) → *брати участь* (correct).

2. **Vocabulary Level Check:**
   - *Trigger:* You are writing for A1/A2 and want to ensure words are level-appropriate.
   - *Action:* Use `rag_query_cefr_level` to verify the word's CEFR level.

3. **Grammar & Morphology Doubts:**
   - *Trigger:* You are unsure about a case ending, irregular plural, or conjugation.
   - *Action:* Use `rag_verify_lemma` to pull the complete declension/conjugation.

4. **Natural Expressions:**
   - *Trigger:* You need a natural idiom or collocation for a dialogue.
   - *Action:* Use `rag_search_idioms` for Ukrainian expressions, `rag_search_synonyms` for word variety.

5. **Drafting Grammar Rules:**
   - *Trigger:* You are explaining a spelling or phonetic rule.
   - *Action:* Use `rag_query_pravopys` to confirm the exact 2019 standard.

6. **Checking Collocations & Frequency:**
   - *Trigger:* You want to confirm a word combination is actually used by native speakers.
   - *Action:* Use `rag_query_grac` with mode='collocations' to see real-world usage.

**Efficiency Rules:**
- **Batch your checks:** Use `rag_verify_words` with 5-15 words at once.
- **Do NOT verify basic words:** *мама*, *стіл*, *робити* don't need checking.
- **Zero invention:** If VESUM doesn't know a word, don't use it.
- **Target: 8-15 tool calls per module**, not 50.

IMPORTANT: After using tools, output your COMPLETE module content as plain text. Do NOT narrate your tool usage. Just output the final module content.


**Verification checklist:**
1. Run `verify_words` on all Ukrainian words in your exercises — every word must exist in VESUM
2. Run `query_cefr_level` on any word you're unsure about — it must be a1-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
