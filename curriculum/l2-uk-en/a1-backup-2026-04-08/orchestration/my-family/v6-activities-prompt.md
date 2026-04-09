<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/my-family.yaml` file for module **6: My Family** (a1).

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

- `<!-- INJECT_ACTIVITY: match-family-vocab -->`
- `<!-- INJECT_ACTIVITY: quiz-u-tebe-ye -->`
- `<!-- INJECT_ACTIVITY: fill-in-possessives -->`
- `<!-- INJECT_ACTIVITY: fill-in-family-dialogue -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'У тебе є...? — answer Так/Ні. Use ONLY the chunk ''у тебе є''. Example questions:
    ''У тебе є брат?'', ''У тебе є сестра?'', ''У тебе є бабуся?'' Answer options:
    ''Так, у мене є брат.'' / ''Ні.'' / ''Так, у мене є два брати.'' Do NOT use genitive
    names (no ''У Оксани є'').'
  items: 6
  type: quiz
- focus: 'Choose correct possessive pronoun. EXACT pattern: ''Це {___} мама.'' → моя
    | ''Де {___} тато?'' → твій | ''Ось {___} батьки.'' → мої All nominative case.
    Options: мій/моя/моє/мої or твій/твоя/твоє/твої.'
  items: 8
  type: fill-in
- focus: 'Match English family words to Ukrainian. Pairs: parents↔батьки, uncle↔дядько,
    aunt↔тітка, grandfather↔дідусь, grandmother↔бабуся, brother↔брат, sister↔сестра,
    mother and father↔мама і тато.'
  items: 8
  type: match-up
- focus: 'Complete a family introduction dialogue with blanks. Pattern: ''— Привіт!
    Це {твій} брат?'' / ''— Так, це мій брат. Ось мій {тато}.'' Options per blank:
    family members or possessives. NO genitive forms.'
  items: 4
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- батьки (parents)
- дядько (uncle)
- тітка (aunt)
- дочка (daughter)
- син (son)
- дружина (wife)
- чоловік (man / husband)
- його (his — doesn't change)
- її (her — doesn't change)
- один, одна (one — m/f)
- два, дві (two — m/f)
- чи (or — in questions)
- тільки (only)
required:
- сім'я (family) — apostrophe word
- мама (mother)
- тато (father)
- брат (brother)
- сестра (sister)
- бабуся (grandmother)
- дідусь (grandfather)
- мій, моя, моє, мої (my — m/f/n/pl)
- твій, твоя, твоє (your — m/f/n, informal)
- у мене є (I have)
- у тебе є (you have, informal)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

After class, two classmates — **Оля** and **Марк** — sit together scrolling through photos on a phone. Оля spots a group picture and asks about Марк's family. This is the most natural way to talk about siblings in Ukrainian: you ask **«У тебе є брати чи сестри?»** (Do you have brothers or sisters?) and answer with **«У мене є...»** (I have...). The little word **чи** (or) connects the two options in the question.

> **Оля:** У тебе є брати чи сестри? *(Do you have brothers or sisters?)*
> **Марк:** Так, у мене є два брати і одна сестра. *(Yes, I have two brothers and one sister.)*
> **Оля:** Ого! У мене тільки один брат. *(Wow! I only have one brother.)*
> **Оля:** Як його звати? *(What's his name?)*
> **Марк:** Коля. А твоя сестра? *(Kolya. And your sister?)*
> **Оля:** Її звати Даша. *(Her name is Dasha.)*

Notice two things here. First, **чи** works like "or" inside yes-or-no questions — you'll hear it constantly in Ukrainian conversation. Second, the number "one" changes by gender: **один брат** (masculine) but **одна сестра** (feminine).

Марк swipes to the next photo — a full family picture from a birthday celebration. He turns the screen toward Оля and starts pointing at faces. This is where the structure **«Це моя...»** (This is my...) becomes essential: it's how you introduce people by name and role.

> **Марк:** Це моя сім'я на фотографії. *(This is my family in the photo.)*
> **Оля:** Класно! Хто це? *(Cool! Who is this?)*
> **Марк:** Це моя мама Марина. *(This is my mom Maryna.)*
> **Марк:** Це мій тато Євген. *(This is my dad Yevhen.)*
> **Марк:** Це моя сестра Катя і мої брати — Іван і Денис. *(This is my sister Katia and my brothers — Ivan and Denys.)*
> **Оля:** А це твоя бабуся? *(And is this your grandmother?)*
> **Марк:** Так, її звати Тетяна. *(Yes, her name is Tetiana.)*
> **Оля:** Яка гарна родина! *(What a lovely family!)*

Оля uses **родина** here, while Марк said **сім'я** earlier — both words mean "family" and both are completely natural. Ukrainians use them interchangeably every day.

Now imagine you need to introduce your own family in a few sentences — at a language exchange, in a message to a Ukrainian friend, or in class. Here is what that sounds like when you combine all the skills from A1.1 so far: self-introduction, city, family members, and possession.

> **Оля:** Привіт! Мене звати Оля. *(Hi! My name is Olya.)*
> **Оля:** Я з Києва. *(I'm from Kyiv.)*
> **Оля:** Моя мама — вчителька. *(My mom is a teacher.)*
> **Оля:** Її звати Олена. *(Her name is Olena.)*
> **Оля:** Мій тато — інженер. *(My dad is an engineer.)*
> **Оля:** Його звати Петро. *(His name is Petro.)*
> **Оля:** У мене є один брат. *(I have one brother.)*
> **Оля:** Його звати Коля. *(His name is Kolya.)*
> **Оля:** Це моя сім'я. *(This is my family.)*

This is a learnable template: name → city → family members → possession. You can swap in your own details and have a ready-made self-presentation.

## Сім'я (Family Vocabulary)

Ukrainian has two words for "family" — **сім'я** and **родина**. Both are used by native speakers; neither is more correct than the other. A Grade 1 textbook by Захарійчук uses both in the same lesson: the section title says «Я і моя **родина**» while the poem inside says «В мене дружна є **сім'я**». Notice the apostrophe in **сім'я** — it separates the **м** from the **я** and is a feature of Ukrainian spelling you'll see often.

The core nuclear family words are: **мама** (mother; the more formal/literary word is **мати**), **тато** (father; formally **батько**), **брат** (brother), **сестра** (sister), **син** (son), **дочка** (daughter; **донька** is a warmer, colloquial variant). You already know how to present them: **Це мій брат. Це моя сестра. Це мій тато.**

Extended family: **бабуся** (grandmother; colloquially also **баба**), **дідусь** (grandfather; colloquially **дід**), **тітка** (aunt), **дядько** (uncle). One important cultural note: Ukrainian has no single word for "grandparents" — you always say **бабуся і дідусь** as a pair. The Захарійчук Grade 1 poem captures the affectionate diminutive forms perfectly: «Люба мама і татусь, / Бабця Віра і дідусь» — here **татусь** is a warm form of **тато** and **бабця** is a variant of **бабуся**.

A few more useful words: **батьки** (parents) is always plural — say **мої батьки**, not *мої мама і тато*. **Дружина** means "wife." **Чоловік** means both "husband" and "man" — context tells you which: **Це мій чоловік** (This is my husband) versus **Там стоїть чоловік** (A man is standing there). And remember: **дочка** is the more common everyday form, while **донька** carries a warm, affectionate tone.

<!-- INJECT_ACTIVITY: match-family-vocab -->

## У мене є (I Have)

Ukrainian expresses possession completely differently from English. There is no verb meaning "to have" the way English uses "have." Instead, Ukrainian says literally "At me there-is" — **У мене є брат** (I have a brother). Break this structure down: **у** means "at" or "by" (indicating where the possession exists), **мене** is the form of "me" used after **у** (this is a frozen chunk — don't worry about why it changes), and **є** means "there is" or "there are." The word **є** is the present-tense form of "to be" — and it stays the same for all persons, singular and plural. Three forms to learn as ready-made chunks: **У мене є** (I have), **У тебе є** (you have — informal), **У вас є** (you have — formal or plural). Examples: **У мене є одна сестра.** **У тебе є брат?** **У вас є діти?**

Asking questions is simple. In Ukrainian, you turn a statement into a question just by raising your intonation at the end — no word order changes needed. **У тебе є сестра? ↗** The answers are straightforward: **Так, у мене є сестра.** / **Так, у мене є два брати.** / **Ні.** / **Ні, у мене тільки один брат.** The word **тільки** (only) is very useful in real conversation. You'll hear it all the time: **У мене тільки одна сестра.** **У мене тільки один брат.**

You might wonder: how do you say "I don't have"? The word **немає** means "there is not," but it requires a grammatical form called the genitive case — which changes the ending of the noun after it. That belongs to A2. For now, the simplest and most natural way to say "no" is just **Ні** or **Ні, у мене тільки...** Native speakers use these short answers in casual conversation constantly.

A quick preview of numbers with family members. **Один** and **одна** change to match gender: **один брат** (masculine), **одна сестра** (feminine). The same pattern applies to "two": **два** and **дві** — **два брати** (masculine), **дві сестри** (feminine). You don't need to memorize a rule — just notice the pattern as it appears: **У мене є два брати і дві сестри.**

<!-- INJECT_ACTIVITY: quiz-u-tebe-ye -->

## Мій, моя, моє (Possessive Pronouns)

The core rule: possessive pronouns match the gender of the thing you possess — not the gender of the speaker. A man still says **моя сестра** (my sister), because **сестра** is a feminine noun. Ukrainian Grade 3 textbooks by Вашуленко teach this as the gender test for nouns: if you can say **мій** before it, it's masculine; **моя** — feminine; **моє** — neuter. Four forms to know: **мій** (masculine) — **мій брат, мій тато, мій дядько**; **моя** (feminine) — **моя сестра, моя мама, моя бабуся**; **моє** (neuter) — **моє місто, моє фото**; **мої** (plural) — **мої батьки, мої брати, мої сестри**. The ending mirrors the noun's gender, not who is speaking.

**Твій, твоя, твоє, твої** work exactly the same way — they mean "your" (informal). **Це твій брат?** **Де твоя мама?** **Це твоє фото?** **Це твої батьки?** Use these forms with people you address as **ти** — friends, family, children. Here's a natural mini-exchange: **— Це мій тато. — Це твій тато? — Так, це мій тато.** / **— Ні, це не мій тато, це мій дядько.**

**Його** (his) and **її** (her) are different — they never change form. **Це його мама. Це його тато. Це його сестра.** **Це її брат. Це її місто.** No matter what gender the noun is, **його** and **її** stay exactly the same. Compare this to **мій/моя/моє**, which always change to match.

The forms **наш** (our), **ваш** (your — formal/plural), and **їхній** (their) belong to A2, where you'll learn the full paradigm with case changes. At A1, use only **мій/твій/його/її** in the nominative.

<!-- INJECT_ACTIVITY: fill-in-possessives -->

<!-- INJECT_ACTIVITY: fill-in-family-dialogue -->

## Підсумок — Summary

**Перевір себе (Self-check):**

- Назви 5 членів сім'ї українською. *(мама, тато, брат, сестра, бабуся...)*
- Як сказати "I have a sister" по-українськи? *(У мене є сестра.)*
- Яка різниця між **мій** і **моя**? *(мій = masculine noun, моя = feminine noun)*
- Як сказати "his" і "her"? Чи вони змінюються? *(його, її — не змінюються)*
- Познайом свою сім'ю у 4–5 реченнях. Зразок:

> **Ти:** Привіт! Мене звати Карен. *(Hi! My name is Karen.)*
> **Ти:** У мене є мама, тато і один брат. *(I have a mom, dad, and one brother.)*
> **Ти:** Моя мама — лікарка. *(My mom is a doctor.)*
> **Ти:** Мій брат — студент. *(My brother is a student.)*
> **Ти:** Це моя сім'я. *(This is my family.)*

Use this as a template — swap in your real family, your real names, your real details. This is yours now.

**Що далі?** In Module 7 (Checkpoint — First Contact), you will combine everything from A1.1: alphabet, sounds, self-introduction, and family — in a full communicative checkpoint.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: my-family
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

**Level: A1.1 (Module 6/55) — COMPLETE BEGINNER**

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

### Pattern: grammar-cases
- **fill-in** — Який відмінок?: Fill in the correct case ending for a noun in context
  - Instruction: *Вставте іменник у правильній формі*
- **quiz** — Визнач відмінок: Identify which case a highlighted noun is in
- **group-sort** — Розподіли за відмінками: Sort noun forms by their case
- **error-correction** — Знайди помилку у відмінку: Find wrong case ending and correct it

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
