<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/checkpoint-first-contact.yaml` file for module **7: Checkpoint: First Contact** (a1).

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

- `<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->`
- `<!-- INJECT_ACTIVITY: fill-in-self-intro -->`
- `<!-- INJECT_ACTIVITY: match-questions-answers -->`
- `<!-- INJECT_ACTIVITY: quiz-comprehensive-review -->`

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

Перевір себе — ти вже знаєш більше, ніж думаєш. This module is not a test. It is a mirror. You have spent six modules building the foundation of your Ukrainian — sounds, letters, soft signs, stress, greetings, and family. Before moving forward, take a moment to look back honestly. Ask yourself each of these questions:

- **Can I read any Ukrainian word aloud?** Think of words like **читати** (to read), **молоко** (milk), **зупинка** (stop). If you can sound them out without hesitation, M01 and M02 did their job.
- **Do I understand what the soft sign and apostrophe do?** The soft sign (ь) softens the preceding consonant: **сіль** (salt), **день** (day). The apostrophe separates a consonant from a following vowel: **м'яч** (ball), **сім'я** (family).
- **Can I place stress correctly?** Stress changes meaning: **руки** (hands — stress on the second syllable) versus **руки** (of a hand — stress on the first). Can you hear the difference in **сестра** (sister)?
- **Can I introduce myself to someone new?** Try it now: **Як тебе звати?** (What is your name?) — **Мене звати Олена.** (My name is Olena.)
- **Can I talk about my family?** For example: **Мій тато — лікар.** (My dad is a doctor.) **Моя мама — вчителька.** (My mom is a teacher.)
- **Do all six feel comfortable?** If yes — congratulations, A1.1 is essentially complete. If one or two feel shaky, that is perfectly normal. The reading practice below will reinforce everything. Навіть якщо ти читаєш повільно — це нормально. Reading becomes faster with practice.

## Читання (Reading Practice)

Read the following text aloud at least twice. The first time, focus on pronouncing each word correctly — sound out every letter. The second time, focus on understanding the meaning. Every word here comes from M01–M06. There is nothing new.

> Привіт! Мене звати Дарина. Я — студентка. Я з Харкова. Моя сім'я живе у Львові. Моя мама — лікарка. Мій тато — інженер. У мене є старший брат. Його звати Михайло. Михайло — програміст. Він працює у Києві. У мене є бабуся і дідусь. Вони живуть у селі. Я дуже люблю свою родину. А ти? Розкажи про свою сім'ю!

*(Hi! My name is Daryna. I am a student. I am from Kharkiv. My family lives in Lviv. My mom is a doctor. My dad is an engineer. I have an older brother. His name is Mykhailo. Mykhailo is a programmer. He works in Kyiv. I have a grandmother and a grandfather. They live in a village. I love my family very much. And you? Tell me about your family!)*

Now close the translation and answer these three questions in full Ukrainian sentences. Do not look back at the text:

- **Як звати дівчину?** (What is the girl's name?)
- **Звідки вона?** (Where is she from?)
- **Ким працює її тато?** (What does her dad do for work?)

Two words in this passage deserve special attention for their stress: **лікарка** has stress on the second syllable, and **інженер** has stress on the final syllable. Stress is the rhythm of Ukrainian — when you read aloud, let it guide your pacing.

<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->

## Граматика (Grammar Summary)

This is not new grammar. It is a pattern map — six constructions you already use, now gathered in one place so you can see how they connect.

**1. Identification — Це + noun**
Point at something and name it: **Це Оля.** (This is Olia.) **Це мій брат.** (This is my brother.)

**2. Description without "is" — Subject + noun**
Ukrainian drops the verb "to be" in present tense: **Я — студент.** (I am a student.) **Мама — лікарка.** (Mom is a doctor.) The dash (—) replaces the missing verb.

**3. Possession — У мене є + noun**
To say you have something: **У мене є сестра.** (I have a sister.) **У мене є кішка.** (I have a cat.)

**4. Asking a name — Як тебе/вас звати?**
Informal: **Як тебе звати?** Formal: **Як вас звати?** The answer always follows the same shape: **Мене звати Тарас.** (My name is Taras.) **Його звати Олексій.** (His name is Oleksii.)

**5. Possessive pronoun — Мій/моя/моє + noun**
The possessive changes to match the noun's gender, just as Ukrainian textbooks teach: if you can say **мій** and **він** — the noun is masculine. If **моя** and **вона** — feminine. If **моє** and **воно** — neuter. **Мій тато.** **Моя мама.** **Моє ім'я** (my name).

**6. Origin as a chunk — Звідки ти? — Я з...**
Ask where someone is from: **Звідки ти?** Answer as one block: **Я з Одеси.** (I am from Odesa.) **Я з Канади.** (I am from Canada.)

One key insight ties these patterns together: Ukrainian does not use a verb "to be" in present-tense identification. **Він — лікар** means "He is a doctor." If you feel the urge to add **є**, resist it — the dash does the work.

## Діалог (Capstone Dialogue)

Imagine you are at a university gathering in Lviv. You meet someone you have never spoken to before. Here is how that first conversation might go. Both speakers are students — the setting is natural, not a classroom drill.

> **Богдан:** Привіт! Я — Богдан. Як тебе звати? *(Hi! I'm Bohdan. What's your name?)*
> **Соломія:** Привіт, Богдане! Мене звати Соломія. *(Hi, Bohdane! My name is Solomiia.)*
> **Богдан:** Дуже приємно! Звідки ти, Соломіє? *(Nice to meet you! Where are you from, Solomiia?)*
> **Соломія:** Я з Тернополя. А ти? *(I'm from Ternopil. And you?)*
> **Богдан:** Я з Дніпра. *(I'm from Dnipro.)*
> **Соломія:** Ти студент? *(Are you a student?)*
> **Богдан:** Так, я — студент. А ти? *(Yes, I'm a student. And you?)*
> **Соломія:** Я теж студентка. *(I'm a student too.)*
> **Богдан:** Цікаво! Моя мама — лікарка. *(Interesting! My mom is a doctor.)*
> **Соломія:** Справді? А твій тато? *(Really? And your dad?)*
> **Богдан:** Мій тато — вчитель. А у тебе? *(My dad is a teacher. And yours?)*
> **Соломія:** Мій тато — інженер. *(My dad is an engineer.)*
> **Богдан:** У тебе є брати чи сестри? *(Do you have brothers or sisters?)*
> **Соломія:** Так, у мене є молодша сестра. Її звати Ганна. *(Yes, I have a younger sister. Her name is Hanna.)*
> **Богдан:** Приємно познайомитись, Соломіє! *(Nice to meet you, Solomiia!)*
> **Соломія:** І мені приємно. До зустрічі! *(Nice to meet you too. See you!)*

Without rereading the dialogue, answer these questions:

- **Звідки Богдан?** (Where is Bohdan from?)
- **Ким працює тато Богдана?** (What does Bohdan's dad do?)
- **Як звати сестру Соломії?** (What is Solomiia's sister's name?)
- **Ким працює тато Соломії?** (What does Solomiia's dad do?)

### Your Graduation Monologue

Now it is your turn. Fill in this template with your own information. This is your connected self-introduction — read it aloud without stopping.

> Привіт! Мене звати ___. Я — ___ [nationality]. Я живу у ___ [city].
> Я — ___ [profession or student]. Моя мама — ___ [profession]. Мій тато — ___ [profession].
> У мене є ___ [family member]. Його/Її звати ___ [name].
> Я дуже люблю свою родину!

Read your completed monologue aloud once more. If you can say it smoothly, without pausing to think about each word, A1.1 is complete. This monologue is your signature — the first thing you can say when you meet a Ukrainian speaker in real life.

Цей монолог — твій підпис. Ти можеш представити себе українською. Це — справжній початок.

<!-- INJECT_ACTIVITY: fill-in-self-intro -->

<!-- INJECT_ACTIVITY: match-questions-answers -->

<!-- INJECT_ACTIVITY: quiz-comprehensive-review -->

## Підсумок — Summary

Ти завершив A1.1. Here is what you already know — test yourself one last time:

- **Скільки літер в українському алфавіті?** — 33 літери. Six vowels: а, е, и, і, о, у.
- **Що робить м'який знак (ь)?** — It softens the preceding consonant: **сіль** (salt), **день** (day).
- **Що робить апостроф (')?** — It separates a labial consonant from a following vowel: **м'яч** (ball), **сім'я** (family).
- **Привітайся формально та неформально.** — **Добрий день!** (formal) / **Привіт!** (informal).
- **Представ себе у 3–4 реченнях.** — **Мене звати ___.** **Я з ___.** **Я — ___.** **У мене є ___.**
- **Назви членів родини з присвійними займенниками.** — **Мій тато, моя мама, мій брат, моя сестра, мій дідусь, моя бабуся.**

If every answer came easily, you are ready for A1.2 — where Ukrainian sentences get longer and things start to have gender. Next up: **Речі мають рід** (Things Have Gender).

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
