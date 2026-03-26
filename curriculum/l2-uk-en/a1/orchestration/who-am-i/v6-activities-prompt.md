# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/who-am-i.yaml` file for module **5: Who Am I?** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-self-intro -->`
- `<!-- INJECT_ACTIVITY: quiz-formal-informal -->`
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
- програміст, програмістка (programmer m/f)
- журналіст, журналістка (journalist m/f)
- інженер, інженерка (engineer m/f)
- звідки (where from)
- зараз (now, currently)
- друг (friend, male)
- його (his — doesn't change)
- її (her — doesn't change)
- Канада (Canada)
- Німеччина (Germany)
required:
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

You arrive in Ukraine. At the hostel, someone smiles and says hello. At a conference, a colleague extends a hand. At a party, a friend brings someone over and introduces them. Every one of these moments starts the same way — with a name, a place, and a greeting. This module gives you the words for your first real conversations in Ukrainian.

### Dialogue 1 — At a hostel

*Two young travelers meet in the common room of a Kyiv hostel. They are about the same age, so they use informal language.*

> **Марко:** Привіт! Як тебе звати? *(Hi! What's your name?)*
> **Олена:** Мене звати Олена. А тебе? *(My name is Olena. And yours?)*
> **Марко:** Мене звати Марко. Звідки ти? *(My name is Marko. Where are you from?)*
> **Олена:** Я з України. А ти? *(I'm from Ukraine. And you?)*
> **Марко:** Я з Канади. *(I'm from Canada.)*
> **Олена:** Дуже приємно! *(Very pleased to meet you!)*

Notice a few things here. **Тебе** (you, informal) signals that this is a casual conversation between peers. **Звідки** (where from) is how you ask about someone's origin. And **Дуже приємно!** (Very pleased!) is what Ukrainians say after exchanging names — never before.

### Dialogue 2 — At a conference

*Two professionals meet during a coffee break. They don't know each other, so they use formal language.*

> **Петро:** Добрий день! Як вас звати? *(Good day! What is your name?)*
> **Софія:** Мене звати Софія. Дуже приємно! *(My name is Sofiya. Very pleased!)*
> **Петро:** Мене звати Петро. Ви з України? *(My name is Petro. Are you from Ukraine?)*
> **Софія:** Так, я з Києва. *(Yes, I'm from Kyiv.)*

The shift from informal to formal is clear: **вас** (you, formal) replaces **тебе**, and **Ви** (you, formal) replaces **ти**. Use formal language with strangers, older people, and in professional settings. Use informal language with friends, peers, and children.

### Dialogue 3 — Introducing someone else

*At a party, your friend introduces two people.*

> **Оксана:** Це мій друг Андрій. *(This is my friend Andriy.)*
> **Оксана:** Він зі Львова. Він — інженер. *(He's from Lviv. He's an engineer.)*
> **Оксана:** А це Катерина. *(And this is Kateryna.)*
> **Оксана:** Вона з Одеси. Вона — журналістка. *(She's from Odesa. She's a journalist.)*

A new pattern appears here: **Це** (this is) + a name to introduce someone. Then **Він** (he) or **Вона** (she) for details about that person. And the profession comes without any verb — just **Він — інженер**, with a dash where English would say "is."

### Informal vs. Formal — Quick Reference

| Situation | Informal | Formal |
|-----------|----------|--------|
| Greeting | **Привіт!** | **Добрий день!** |
| What's your name? | **Як тебе звати?** | **Як вас звати?** |
| Where from? | **Звідки ти?** | **Звідки ви?** |
| You are from... | **Ти з...** | **Ви з...** |

The Grade 1 Ukrainian textbook shows this same first-meeting pattern: «Мене звати Ганна. Привіт! Я Тарас.» From day one, Ukrainian children learn to introduce themselves with exactly these phrases.

## Мене звати... (My name is...)

The phrase **Мене звати** literally means "me they-call." There is no verb "to be" anywhere in this construction. Ukrainian does not say "My name IS Marko" — it says **Мене звати Марко**, which is closer to "Me-they-call Marko." English needs three words — "my name is" — while Ukrainian needs just two: **мене звати**. This is your first glimpse of how Ukrainian builds sentences differently from English. More examples: **Мене звати Олена.** **Мене звати Тарас.** **Мене звати Софія.**

To ask the question, put **Як** (how) at the front. Informally: **Як тебе звати?** Formally: **Як вас звати?** You can also ask about other people. **Як його звати?** (What's his name?) uses **його** (his). **Як її звати?** (What's her name?) uses **її** (her). Both **його** and **її** never change form — they stay the same no matter how you use them. Here is a quick exchange showing this:

> **Оленка:** Хто це? *(Who is this?)*
> **Тарас:** Це Андрій. *(This is Andriy.)*
> **Оленка:** Як його звати? *(What's his name?)*
> **Тарас:** Його звати Андрій. *(His name is Andriy.)*

Ukrainians also use a shorter form in casual speech. Instead of **Мене звати Олена**, you can simply say **Я — Олена** or even just **Я Олена**, dropping **звати** entirely. This is common and perfectly correct. Both forms work: **Мене звати Олена** = **Я Олена**.

After exchanging names, Ukrainians say **Дуже приємно!** (Very pleasant!) or **Приємно познайомитись!** (Pleasant to get acquainted!). The other person responds **Мені також!** (Me too!). This greeting always comes AFTER names are exchanged, not before.

<!-- INJECT_ACTIVITY: fill-in-self-intro -->

## Це... (This is...)

The word **Це** (this is) does the work of several English phrases all by itself. It means "this is," "it is," and even "these are" — and it never needs a verb. Just **Це** + a noun:

- **Це кава.** (This is coffee.)
- **Це Київ.** (This is Kyiv.)
- **Це мій друг.** (This is my friend.)
- **Це моя сестра.** (This is my sister.)
- **Це студенти.** (These are students.)

Notice that **Це** works for both singular and plural — no change needed. One word handles everything.

To ask questions with **Це**, use **Що це?** (What is this?) for things and **Хто це?** (Who is this?) for people. The question word always goes first: **Хто це?** — never *Це хто? Here is a quick practice exchange:

> **Марко:** Що це? *(What is this?)*
> **Олена:** Це кава. *(This is coffee.)*
> **Марко:** А хто це? *(And who is this?)*
> **Олена:** Це Тарас. *(This is Taras.)*

The Grade 1 textbook teaches exactly this distinction: **Хто це?** for living things (people, animals), **Що це?** for objects.

To say "this is NOT," add **не** (not) before the noun. No verb to negate — you simply place **не** between **Це** and the noun:

- **Це не чай, це кава.** (This is not tea, this is coffee.)
- **Це не Марко, це Андрій.** (This is not Marko, this is Andriy.)
- **Це не вчитель, це лікар.** (This is not a teacher, this is a doctor.)

The pattern is always the same: **Це** + **не** + noun.

<!-- INJECT_ACTIVITY: quiz-formal-informal -->

## Я — студент (I am a student)

Ukrainian has no verb "to be" in the present tense. Where English says "I am a student," Ukrainian says **Я — студент**. The dash (—) marks the pause where "is" would go in English. This is not slang or shorthand — it is standard Ukrainian grammar. Every Ukrainian says it this way:

- **Я — студент.** (I am a student.)
- **Він — лікар.** (He is a doctor.)
- **Вона — вчителька.** (She is a teacher.)
- **Ми — студенти.** (We are students.)

Most Ukrainian professions have separate masculine and feminine forms. The feminine form typically adds **-ка** to the masculine base. Always use the form that matches the person:

| Masculine | Feminine | English |
|-----------|----------|---------|
| **студент** | **студентка** | student |
| **вчитель** | **вчителька** | teacher |
| **лікар** | **лікарка** | doctor |
| **програміст** | **програмістка** | programmer |
| **журналіст** | **журналістка** | journalist |
| **інженер** | **інженерка** | engineer |

**Він — лікар.** **Вона — лікарка.** Always match the form to the person.

Nationalities follow the same gendered pattern:

- **українець** / **українка** (Ukrainian m/f)
- **американець** / **американка** (American m/f)
- **канадієць** / **канадка** (Canadian m/f)

Full sentences: **Я — українець.** **Вона — американка.** **Він — канадієць.** These are nominative forms — the basic "dictionary" form of each word.

<!-- INJECT_ACTIVITY: match-professions -->

## Звідки? (Where from?)

The question **Звідки ти?** (informal) or **Звідки ви?** (formal) means "Where are you from?" The answer follows a simple pattern: **Я з** + country.

- **Я з України.** (I'm from Ukraine.)
- **Я з Канади.** (I'm from Canada.)
- **Я зі Штатів.** (I'm from the States.)
- **Я з Німеччини.** (I'm from Germany.)

Notice **зі** before **Штатів** — Ukrainian uses **зі** instead of **з** before consonant clusters starting with з or с, just like in **зі Львова**. For now, treat these as memorized chunks.

You might notice that country names look different after **з**: **Україна** becomes **України**, **Канада** becomes **Канади**. This happens because of the genitive case — but do not memorize case rules yet. That is A2 grammar. For now, learn each "**з** + country" as a fixed phrase, the same way you memorize a phone number. The key chunks: **з України**, **з Канади**, **зі Штатів**, **з Німеччини**, **з Англії**, **з Франції**.

The same pattern works for cities: **Я з Києва.** **Я зі Львова.** **Я з Одеси.** **Він з Торонто.** Here is a mini-dialogue that combines everything from this module:

> **Джеймс:** Привіт! Як тебе звати? *(Hi! What's your name?)*
> **Софія:** Мене звати Софія. А тебе? *(My name is Sofiya. And yours?)*
> **Джеймс:** Я Джеймс. Звідки ти? *(I'm James. Where are you from?)*
> **Софія:** Я з Києва. Я — студентка. А ти? *(I'm from Kyiv. I'm a student. And you?)*
> **Джеймс:** Я з Канади. Я — програміст. *(I'm from Canada. I'm a programmer.)*
> **Софія:** Дуже приємно! *(Pleased to meet you!)*

<!-- INJECT_ACTIVITY: fill-in-dialogue -->

## Підсумок — Summary

You now have everything you need for a real first conversation in Ukrainian. You can introduce yourself with **Мене звати** + your name, or simply **Я** + name. You can ask someone's name — **Як тебе звати?** for friends, **Як вас звати?** for formal situations. You can identify people and things with **Це**: **Це мій друг. Це кава. Хто це? Що це?** You can state your profession without any verb: **Я — студент. Вона — лікарка. Він — інженер.** And you can say where you are from: **Я з України. Я з Канади. Звідки ти?** Every phrase you learned today works without a verb "to be." That is not a gap in the language — it is how Ukrainian works. Where English says "is," Ukrainian says nothing at all.

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
