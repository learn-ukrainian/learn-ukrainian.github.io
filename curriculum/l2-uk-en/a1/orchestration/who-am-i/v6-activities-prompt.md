<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/who-am-i.yaml` file for module **5: Who Am I?** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-self-intro -->`
- `<!-- INJECT_ACTIVITY: quiz-formal-informal -->`
- `<!-- INJECT_ACTIVITY: match-question-words -->`
- `<!-- INJECT_ACTIVITY: match-professions -->`
- `<!-- INJECT_ACTIVITY: fill-in-dialogue -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Complete self-introduction: Мене звати..., Я з..., Я —...'
  items: 6
  type: fill-in
- focus: Formal or informal? Choose the right introduction.
  items: 6
  type: quiz
- focus: Match professions with male/female forms
  items: 8
  type: match-up
- focus: Complete the dialogue with correct phrases
  items: 6
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- ми (we)
- вони (they)
- програміст, програмістка (programmer m/f)
- інженер, інженерка (engineer m/f)
- звідки (where from)
- друг (friend, male)
- його (his — doesn't change)
- її (her — doesn't change)
- Канада (Canada)
- Німеччина (Germany)
required:
- я (I)
- ти (you, informal)
- він (he)
- вона (she)
- ви (you, formal/plural)
- мене звати (my name is)
- як тебе звати? (what's your name, informal)
- як вас звати? (what's your name, formal)
- це (this is / these are)
- дуже приємно (pleased to meet you)
- студент, студентка (student m/f)
- вчитель, вчителька (teacher m/f)
- лікар, лікарка (doctor m/f)
- українець, українка (Ukrainian m/f)
- Україна (Ukraine)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

Three conversations. Three situations. One goal: introduce yourself in Ukrainian. The first dialogue happens at a hostel — casual, between peers. The second takes place at a conference — formal, between professionals. The third introduces someone else. Read each dialogue, listen to the audio if available, then try repeating the lines out loud. Pay attention to one key difference: **тебе** (you, informal) versus **вас** (you, formal). That single word changes the entire register of the conversation.

### Dialogue 1 — At a Hostel (Informal)

> **Олена:** Привіт! Як тебе звати? *(Hi! What's your name?)*
> **Марко:** Мене звати Марко. А тебе? *(My name is Marko. And yours?)*
> **Олена:** Мене звати Олена. Звідки ти? *(My name is Olena. Where are you from?)*
> **Марко:** Я з Канади. А ти? *(I'm from Canada. And you?)*
> **Олена:** Я з України. Дуже приємно! *(I'm from Ukraine. Pleased to meet you!)*
> **Марко:** Мені також! *(Me too!)*

A few things to absorb before moving on. **Тебе** is the informal "you" — used between friends, peers, and people of similar age. **Звати** means "to call." **Звідки** means "where from." And **Мені також** means "me too" or "likewise" — a natural response after someone says **Дуже приємно!** Don't analyze the grammar yet. Just notice the rhythm of the exchange: name → name → origin → origin → pleasure.

### Dialogue 2 — At a Conference (Formal)

> **Оксана:** Добрий день! Як вас звати? *(Good day! What is your name?)*
> **Петро:** Мене звати Петро Коваленко. Дуже приємно! *(My name is Petro Kovalenko. Pleased to meet you!)*
> **Оксана:** Мені також! Я — Оксана Мельник. Ви з України? *(Likewise! I'm Oksana Melnyk. Are you from Ukraine?)*
> **Петро:** Так, я з Києва. А ви? *(Yes, I'm from Kyiv. And you?)*
> **Оксана:** Я з Канади, але я вчу українську. *(I'm from Canada, but I'm learning Ukrainian.)*

One word changed: **вас** (you, formal) replaced **тебе**. That single swap shifts the entire conversation from casual to professional. **Але** means "but." Notice that Petro uses his full name — first name plus surname. In formal Ukrainian settings, this is standard. Everything else follows the same pattern as Dialogue 1.

### Dialogue 3 — Introducing Someone Else

> **Марта:** Це Андрій. Він зі Львова. Він — інженер. *(This is Andriy. He's from Lviv. He's an engineer.)*
> **Марта:** А це Оксана. Вона з Одеси. Вона — лікарка. *(And this is Oksana. She's from Odesa. She's a doctor.)*
> **Андрій:** Дуже приємно познайомитись! *(Very pleased to meet you!)*

Here the speaker introduces two other people. **Він** means "he." **Вона** means "she." **Інженер** is "engineer" and **лікарка** is "doctor" (female). Notice that **Це** stays the same regardless of who is being introduced — **Це** Андрій, **Це** Оксана. It never changes form.

<!-- INJECT_ACTIVITY: fill-in-self-intro -->

## Мене звати... (My name is...)

Break this phrase apart. **Мене** is the object form of **я** (I) — it means "me." **Звати** means "to call." Put them together: **Мене звати** literally translates as "me they-call." There is no verb "to be" and no word for "my name." Ukrainian doesn't say "My name IS Marko" — it says "Me-they-call Marko." This is not a quirk or a shortcut. It is the standard, textbook-attested way to state your name, used from the very first page of Bolshakova's Grade 1 bukvar: «Мене звати Ганна.» Don't try to construct *Моє ім'я є... — that is an English calque and sounds unnatural in Ukrainian.

To ask someone's name, change the first word. Two registers exist:

Informal: **Як тебе звати?** — use with a child, friend, or peer.
Formal: **Як вас звати?** — use with a stranger, elder, or in a professional setting.

About a third person: **Як його звати?** (asking about a man — **його** means "his") and **Як її звати?** (asking about a woman — **її** means "her"). The pattern is consistent: the slot before **звати** changes with the person, but **звати** itself stays fixed. Example: — **Як його звати?** — **Його звати Богдан.**

One note: you will also hear **Мене звуть** — this is an equally correct variant using a different verb form. Both **мене звати** and **мене звуть** are standard Ukrainian. This curriculum teaches **мене звати** as the primary A1 form.

After both people exchange names, the standard reaction is **Дуже приємно!** — literally "very pleasant," meaning "pleased to meet you." The response is **Мені також!** meaning "me too" or "likewise." A slightly more formal variant is **Приємно познайомитись!** — "pleasant to get acquainted." All three expressions are interchangeable. The key cultural point: say **Дуже приємно** *after* names are exchanged — it is not a greeting, it is a reaction to learning someone's name.

> **Марта:** Мене звати Марта. *(My name is Marta.)*
> **Іван:** Мене звати Іван. Дуже приємно! *(My name is Ivan. Pleased to meet you!)*
> **Марта:** Мені також! *(Likewise!)*

<!-- INJECT_ACTIVITY: quiz-formal-informal -->

## Це... (This is...)

**Це** is the universal pointer word in Ukrainian. It means "this is," "it is," and even "these are" — all in one unchanging form. No gender. No number. No agreement with anything.

**Це кава.** (This is coffee.)
**Це Київ.** (This is Kyiv.)
**Це Андрій.** (This is Andriy.)
**Це студенти.** (These are students.)

Whether you are pointing at a person, a city, or a cup of coffee — **Це** stays the same. Don't try to make it agree with the noun. It doesn't.

Two question words pair with **Це**:

**Що це?** — "What is this?" Use for things, places, and concepts.
**Хто це?** — "Who is this?" Use for people and animals.

There is a critical word-order rule: the question word goes FIRST. **Що це?** ✓ — never *Це що? ✗. **Хто це?** ✓ — never *Це хто? ✗. Model answers:

> — **Що це?** — **Це університет.** *(What is this? — This is a university.)*
> — **Хто це?** — **Це Оксана. Вона — лікарка.** *(Who is this? — This is Oksana. She's a doctor.)*

Negation is simple: insert **не** (not) directly before the noun. **Це не кава. Це чай.** (This is not coffee. This is tea.) **Це не Андрій. Це Тарас.** (This is not Andriy. This is Taras.) Same pattern as the affirmative — just add **не**.

<!-- INJECT_ACTIVITY: match-question-words -->

## Особові займенники (Personal Pronouns)

Seven personal pronouns form the backbone of every Ukrainian sentence. Here they are in the nominative case — the form used for sentence subjects:

| Pronoun | Meaning | Example |
|---------|---------|---------|
| **я** | I | **Я — студентка.** (I am a student.) |
| **ти** | you (informal, singular) | **Ти з Канади?** (Are you from Canada?) |
| **він** | he | **Він — лікар.** (He is a doctor.) |
| **вона** | she | **Вона з Одеси.** (She is from Odesa.) |
| **ми** | we | **Ми з України.** (We are from Ukraine.) |
| **ви** | you (formal singular OR plural) | **Ви з Києва?** (Are you from Kyiv?) |
| **вони** | they | **Вони — студенти.** (They are students.) |

Two cultural notes. First: **ви** does double duty. It means "you all" (plural) AND "you" (polite singular). The same word that addresses a group also shows respect to one person — an elder, a stranger, a professional. Second: in formal written texts like letters or official documents, **Ви** addressing one person is capitalized — you may see both **ви** and **Ви** in Ukrainian writing. These seven pronouns appear in nearly every sentence from this point forward.

## Я — студент (I am a student)

In English: "I **am** a student." In Ukrainian: **Я — студент.** No verb. The dash (—) marks the spot where "is," "am," or "are" would appear in English — but Ukrainian simply omits the verb "to be" in the present tense. This applies across all persons:

**Він — лікар.** (He is a doctor.)
**Вона — вчителька.** (She is a teacher.)
**Ми — студенти.** (We are students.)
**Ти — програміст?** (You are a programmer?)

If you are used to European languages where every sentence needs a verb, this will feel strange. The dash IS the grammar signal. It tells you: subject on the left, identity on the right, no verb needed.

:::tip
The dash in **Я — студент** is not strictly required by grammar when the subject is a pronoun. But Ukrainian textbooks use it regularly as an emphatic marker — and at A1, it helpfully shows where "is" would go. Use it.
:::

Nationalities and professions come in gendered pairs. Memorize them as pairs — don't try to derive one from the other yet.

**Nationalities:** **українець** / **українка** (Ukrainian m/f), **американець** / **американка** (American m/f), **канадієць** / **канадка** (Canadian m/f), **британець** / **британка** (British m/f), **німець** / **німкеня** (German m/f).

**Professions:** **студент** / **студентка** (student m/f), **вчитель** / **вчителька** (teacher m/f), **лікар** / **лікарка** (doctor m/f), **програміст** / **програмістка** (programmer m/f), **інженер** / **інженерка** (engineer m/f), **журналіст** / **журналістка** (journalist m/f).

A pattern to notice: the endings **-ка**, **-ня**, **-иця** often mark the feminine form. For now, just memorize the pairs. The derivation rules are B1 morphology — they can wait.

<!-- INJECT_ACTIVITY: match-professions -->

## Звідки? (Where from?)

The question **Звідки ти?** (informal) or **Звідки ви?** (formal) means "Where are you from?" The answer follows a fixed pattern: **Я з** + country.

**Я з України.** (I'm from Ukraine.)
**Я з Канади.** (I'm from Canada.)
**Я зі Штатів.** (I'm from the States.)
**Я з Німеччини.** (I'm from Germany.)
**Я з Великої Британії.** (I'm from Great Britain.)
**Я з Австралії.** (I'm from Australia.)

Notice that the country names look slightly different from their base forms — **Україна** becomes **України**, **Канада** becomes **Канади**. These are genitive case forms, but you do NOT need to understand genitive grammar yet. Treat **Я з України** as a single memorized chunk, the same way you memorized **Мене звати**. Genitive case is A2 grammar.

One small detail: **з** becomes **зі** before certain consonant clusters. **Зі Львова**, **зі Штатів**. Don't overthink it — your ear will catch the pattern naturally.

Extend the pattern to third person and cities:

**Він з Києва.** (He is from Kyiv.)
**Вона зі Львова.** (She is from Lviv.)
**Вони з Харкова.** (They are from Kharkiv.)

Now combine everything from this module into full "ID sentences" — the production target:

**Це Андрій. Він — інженер. Він з Києва.**
**Це Марта. Вона — лікарка. Вона з Канади.**

Three sentences. Name, profession, origin. You can now introduce any person in Ukrainian.

:::caution
Do not try to say **Де ви живете?** (Where do you live?) yet. That question requires the locative case and verb conjugation — both taught in later modules. **Звідки?** asks about origin and uses a frozen chunk with no conjugation needed.
:::

<!-- INJECT_ACTIVITY: fill-in-dialogue -->

## Підсумок — Summary

You can now do four things in Ukrainian. First, introduce yourself: **Мене звати...** with your name. Second, identify people and things using **Це** — and ask about them with **Хто це?** or **Що це?** Third, state who you are without a verb: **Я — студент**, **Вона — лікарка**. Fourth, say where you are from: **Я з України**, **Він з Києва**. These four structures combine into a complete self-introduction. Try building yours now: **Мене звати [ім'я]. Я з [країна]. Я — [професія].** Practice saying it aloud. In the next module, you will use these same patterns to talk about your family.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: who-am-i
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

**Level: A1.1 (Module 5/55) — COMPLETE BEGINNER**

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
