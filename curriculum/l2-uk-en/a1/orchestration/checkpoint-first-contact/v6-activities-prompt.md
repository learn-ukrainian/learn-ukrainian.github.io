# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/checkpoint-first-contact.yaml` file for module **7: Checkpoint: First Contact** (a1).

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

- `<!-- INJECT_ACTIVITY: match-up -->`
- `<!-- INJECT_ACTIVITY: fill-in -->`
- `<!-- INJECT_ACTIVITY: quiz -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Comprehensive review: sounds, letters, greetings, family'
  items: 12
  type: quiz
- focus: Complete the full self-introduction monologue
  items: 8
  type: fill-in
- focus: Match questions with answers (Як звати? → Мене звати...)
  items: 8
  type: match-up


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- ім'я (first name)
- прізвище (surname)
required:
- All vocabulary from M01-M06 is recycled — no new required words


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Що ми знаємо? (What Do We Know?)

You have successfully reached the end of the first major phase of your Ukrainian learning journey. Over the past six modules, you have mastered the foundational building blocks of the language. You have learned the 33 letters of the Ukrainian alphabet, discovered how the soft sign and the apostrophe change pronunciation, practiced placing word stress, and acquired essential greetings and family vocabulary. This checkpoint is designed to test whether you can combine all these individual skills into fluid, connected speech. There are absolutely no new words introduced here—every single word you will read and say comes directly from the previous modules.

Take a moment to reflect on your progress. Ask yourself the following questions honestly to gauge your readiness: First, can you confidently read any Ukrainian word aloud, recognizing familiar letters without hesitation? Second, do you know exactly what the soft sign does in a word like **день** (day) or **сіль** (salt), and how the apostrophe functions in **сім'я** (family) or **м'який** (soft)? Third, can you correctly identify and emphasize the stressed syllable in words like **мама** (mother), **студент** (student), and **Україна** (Ukraine)? Fourth, are you able to naturally say **Привіт** (Hi), **Мене звати...** (My name is...), and **Я з...** (I am from...)? Finally, can you accurately name your family members using the correct possessive words **мій**, **моя**, or **моє** (my)?

As you work through this module, read every Ukrainian sentence aloud. Try to perform the dialogues from memory before checking the text. Approach this entire section as a helpful self-assessment rather than a strict test. In Ukrainian, we say **«Це не іспит — це дзеркало»** (This isn't a test — it's a mirror). It reflects what you have solidly acquired and what might need a quick review. If any specific area feels slightly weak or hesitant, simply revisit that respective module before continuing to the next phase of the curriculum.

## Читання (Reading Practice)

Now it is time to put your reading skills into practice. Read the following text aloud at a comfortable, steady pace. Every single word in this passage is drawn from your previous lessons, meaning you already possess all the vocabulary required to understand it perfectly. Focus entirely on clear pronunciation, hitting the correct stressed syllables, and reading smoothly without pausing between every letter.

**Привіт!** (Hi!)
**Мене звати Оксана.** (My name is Oksana.)
**Я — студентка.** (I am a student [female].)
**Я з Києва.** (I am from Kyiv.)
**Моя мама — лікарка.** (My mother is a doctor [female].)
**Мій тато — інженер.** (My father is an engineer.)
**У мене є брат.** (I have a brother.)
**Його звати Тарас.** (His name is Taras.)
**Він — учень.** (He is a student [schoolboy].)
**Моя сім'я — невелика, але дружна.** (My family is not large, but friendly.)

Before moving on to the grammatical breakdown, let us do a quick comprehension check to ensure you are grasping the meaning and not merely decoding the sounds. Ask yourself these three simple questions in English: What is Oksana's profession? What does her father do for a living? How many people are explicitly mentioned in her family? Answering these correctly confirms that your brain is successfully connecting the Cyrillic letters to real-world concepts.

Let us put a pronunciation spotlight on a few specific words from the passage that perfectly test your early skills. Look closely at **сім'я** (family). Remember that the apostrophe forces a hard stop before the **я**, preventing the consonants from blending together. Pay attention to the word **звати** (to call), which begins with the consonant cluster **зв-**. You must pronounce both sounds clearly without inserting an extra vowel between them. In the word **невелика** (not large), ensure your voice rises on the stressed syllable **-ли-**. Finally, in the word **інженер** (engineer), remember to keep the consonant **н** slightly soft before the vowel **е**. None of these are new concepts; you practiced each phonetic pattern extensively when learning the alphabet.

## Граматика (Grammar Summary)

Throughout your first encounters with Ukrainian, you have absorbed grammar naturally through repeated exposure. These are the six key patterns you have already learned. You do not need to memorize complex rules at this stage; instead, you simply need to recognize and produce these structures automatically in conversation. Let us review each pattern with examples you already know.

Pattern 1: The word **Це** (This is) followed by a noun is used for basic identification. You can point to someone or something and say **Це мама** (This is mom), **Це брат** (This is brother), or **Це Україна** (This is Ukraine). Notice that no verb corresponding to the English "is" is needed in the Ukrainian sentence.

Pattern 2: When stating a subject and a noun directly, Ukrainian uses a grammatical dash instead of the verb "to be." You say **Я — студент** (I am a student), **Вона — лікарка** (She is a doctor), or **Тарас — учень** (Taras is a student). The dash functionally replaces the English word "is" or "am."

Pattern 3: To express possession, you use the structure **У мене є** (I have) followed by a noun. You say **У мене є брат** (I have a brother) or **У мене є сім'я** (I have a family). Literally translated, Ukrainian says "by me there is" rather than using a direct verb for "have."

Pattern 4: Asking for someone's name requires specific fixed phrases depending on the level of formality. In informal situations, you ask **Як тебе звати?** (What is your name?). The response is **Мене звати Оксана** (My name is Oksana). In formal situations, you shift to **Як вас звати?** (What is your name?). The response remains the same: **Мене звати Іван** (My name is Ivan).

Pattern 5: Possessive words must align with the noun they describe. You use **мій**, **моя**, or **моє** (my) depending on the gender of the family member or object. You say **Мій тато** (My father) because it is masculine. You say **Моя мама** (My mother) because it is feminine. You say **Моє ім'я** (My name) because it is neuter.

Pattern 6: Stating your origin uses the question **Звідки ти?** (Where are you from?) and the answer format **Я з...** (I am from...). You say **Я з Києва** (I am from Kyiv) or **Я з Канади** (I am from Canada). You have learned this as a fixed conversational chunk, and the full grammar rules for how place names change endings will be explored later in your studies.

## Діалог (Capstone Dialogue)

This is the capstone dialogue for your first major milestone. It combines every single communicative skill you have acquired into one cohesive, natural conversation. The setting is simple: two people meet for the first time at a **мовний клуб** (language club). Read both roles aloud, practicing the rhythm of a real exchange.

> **Андрій:** Привіт! *(Hi!)*
> **Софія:** Добрий день! *(Good day!)*
> **Андрій:** Як тебе звати? *(What is your name?)*
> **Софія:** Мене звати Софія. А тебе? *(My name is Sofia. And you?)*
> **Андрій:** Мене звати Андрій. Звідки ти? *(My name is Andriy. Where are you from?)*
> **Софія:** Я з Львова. А ти? *(I am from Lviv. And you?)*
> **Андрій:** Я з Торонто. Я — програміст. А ти? *(I am from Toronto. I am a programmer. And you?)*
> **Софія:** Я — вчителька. *(I am a teacher.)*
> **Андрій:** У тебе є сім'я? *(Do you have a family?)*
> **Софія:** Так, у мене є мама, тато і сестра. *(Yes, I have a mom, a dad, and a sister.)*
> **Андрій:** Це моя сестра. Її звати Марія. *(This is my sister. Her name is Mariia.)*
> **Софія:** Дуже приємно! Бувай! *(Very nice to meet you! Bye!)*
> **Андрій:** До побачення! *(Goodbye!)*

Notice how this conversation flows naturally by building on simple blocks. It uses the informal register, employing words like **ти** (you), **Привіт** (Hi), and **Бувай** (Bye). The exchange relies heavily on question-answer pairs, and you can see how each grammatical pattern from the previous section appears naturally in context. Pay special attention to the echoing structure: **А ти?** (And you?) or **А ви?** (And you? [formal]). Ukrainian conversations frequently mirror questions back to keep the dialogue active.

<!-- INJECT_ACTIVITY: match-up -->

Now it is time to transition from reading a dialogue to delivering a monologue. It is your turn to speak. Instead of a back-and-forth conversation between two people, your goal is to produce a connected self-introduction. Consider this your graduation speech for this level—it represents everything you can confidently say about yourself in Ukrainian right now.

Here is a model monologue showing what a complete introduction looks like, followed by a template with gaps for your personal information. First, review this completed example spoken by a fictional character:

**Привіт! Мене звати Олена. Я з Відня. Я — студентка. Моя мама — лікарка. Мій тато — інженер. У мене є брат. Його звати Іван. Моя сім'я — велика. Дуже приємно!** (Hi! My name is Olena. I am from Vienna. I am a student. My mom is a doctor. My dad is an engineer. I have a brother. His name is Ivan. My family is large. Very nice to meet you!)

Now, use this template to introduce yourself:
**Привіт! Мене звати ___. Я з ___. Я — ___. Моя мама — ___. Мій тато — ___. У мене є ___. Його/Її звати ___. Моя сім'я — ___. Дуже приємно!**

<!-- INJECT_ACTIVITY: fill-in -->

To truly cement this skill, practice speaking your monologue aloud three times. The first time, simply read directly from the template, filling in your specific details. The second time, look away and glance back at the text only when you get stuck. The third time, perform it entirely from memory. If you can complete the third round smoothly, you have fully graduated this phase. As you speak, remember that small details matter: word stress changes how professional you sound, the apostrophe in **сім'я** (family) requires a hard pause, and the soft sign in **день** (day) completely changes the final consonant sound.

## Підсумок — Summary

To conclude this checkpoint, test yourself against these four final questions. One: How many letters are in the Ukrainian alphabet? (The answer is 33). How many sounds does it have? (The answer is 38). Two: Can you greet someone formally and informally? (**Добрий день** for formal, **Привіт** for informal). Three: Can you introduce yourself in five connected sentences covering your name, origin, profession, one family member, and a goodbye? Four: Can you pair the correct possessive words **мій**, **моя**, and **моє** with a family member or object representing each grammatical gender?

If you could answer all four questions confidently, you are perfectly prepared for the next stage. Moving forward, Ukrainian introduces its first major grammatical framework: grammatical gender. Everything you have learned so far has relied on memorized chunks and conversational patterns. Starting in the next module, you will finally understand the deeper mechanics of the language and exactly WHY we say **моя мама** (my mother) but **мій тато** (my father). We will see you in the next step: **Речі мають рід** (Things Have Gender).

<!-- INJECT_ACTIVITY: quiz -->

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: checkpoint-first-contact
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

**Level: A1.1 (Module 7/55) — COMPLETE BEGINNER**

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


## Quality Rules

1. **Instructions match learner level:**
   - **A1.1 (M01-M07):** Instructions in ENGLISH. The learner is a complete beginner who cannot read Ukrainian yet. They are learning the alphabet and first words. Use activity types: image-to-letter, letter-grid, match-up (letter↔sound), quiz (in English about Ukrainian sounds/letters). Anna Ohoiko's pronunciation videos should be referenced where relevant.
   - **A1.2-A1.3 (M08-M21):** Instructions in simple English with Ukrainian key terms in bold. Learner knows basic words but not grammar terminology.
   - **A1.4+ (M22-M55):** Instructions can be in simple Ukrainian with English translation in parentheses.
   - **A2+:** Instructions in Ukrainian.
   - **B1+:** Full Ukrainian, no English.
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

**Efficiency Rules:**
- **Batch your checks:** Use `mcp__rag__verify_words` with 5-15 words at once.
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
