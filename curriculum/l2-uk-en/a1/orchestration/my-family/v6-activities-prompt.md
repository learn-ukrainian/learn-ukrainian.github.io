# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/my-family.yaml` file for module **6: My Family** (a1).

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

- `<!-- INJECT_ACTIVITY: match-family-vocab -->`
- `<!-- INJECT_ACTIVITY: quiz-u-tebe-ye -->`
- `<!-- INJECT_ACTIVITY: fill-in-possessives -->`
- `<!-- INJECT_ACTIVITY: fill-in-dialogue -->`

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

Оля and Максим sit in a cafe. Maksym pulls out his phone — he has new photos from a family gathering. Showing phone photos to friends is universal, and in Ukraine it often turns into a full family introduction.

> **Оля:** У тебе є брати чи сестри? *(Do you have brothers or sisters?)*
> **Максим:** Так, у мене є два брати і одна сестра. *(Yes, I have two brothers and one sister.)*
> **Оля:** Ого! У мене тільки один брат. *(Wow! I only have one brother.)*
> **Оля:** Як його звати? *(What's his name?)*
> **Максим:** Коля. *(Kolya.)*

A few words to notice: **чи** (or) appears in yes/no questions when offering a choice. **Тільки** (only) is a useful word — it softens a statement. **Як його звати?** literally means "How is he called?" — you already know **Як тебе звати?** from Module 5, and **його** (his/him) simply replaces **тебе** (you).

Maksym swipes to a group photo. Ukrainians often keep extended family photos on their phones — family ties run deep.

> **Максим:** Це моя сім'я на фотографії. *(This is my family in a photo.)*
> **Оля:** Класно! Хто це? *(Cool! Who is this?)*
> **Максим:** Це моя мама Марина. *(This is my mom Maryna.)*
> **Максим:** Це мій тато Євген. *(This is my dad Yevhen.)*
> **Максим:** Це моя сестра Катя. *(This is my sister Katia.)*
> **Максим:** І мої брати — Іван і Денис. *(And my brothers — Ivan and Denys.)*
> **Оля:** А це твоя бабуся? *(And is this your grandmother?)*
> **Максим:** Так, її звати Тетяна. *(Yes, her name is Tetiana.)*

**Хто це?** (Who is this?) is your go-to question when pointing at someone in a photo. **Її звати** (her name is) works exactly like **його звати** — just swap the pronoun.

Notice the pattern **Це** + possessive + noun: **Це мій тато**, **Це моя мама**, **Це мої брати**. Ukrainian uses **Це** (this is) the same way English uses "This is" for introductions. Already you can see that **мій** and **моя** are different — we will explore why in the possessive pronouns section below.

Now Оля introduces her own family — a connected monologue combining everything from Modules 1–5 with new family vocabulary:

> **Оля:** Привіт! Мене звати Оля. *(Hi! My name is Olya.)*
> **Оля:** Моя мама — вчителька. *(My mom is a teacher.)*
> **Оля:** Мій тато — інженер. *(My dad is an engineer.)*
> **Оля:** У мене є один брат. *(I have one brother.)*
> **Оля:** Його звати Андрій. *(His name is Andriy.)*
> **Оля:** Моя бабуся Ганна живе в Києві. *(My grandmother Hanna lives in Kyiv.)*
> **Оля:** У мене дружна сім'я. *(I have a close-knit family.)*

Three key patterns carry this entire module. First: **У мене є** + family member for saying what family you have. Second: **Це мій/моя** + person for introducing someone. Third: **Як його/її звати?** → **Його/Її звати...** for asking and giving names. Master these three and you can talk about any family.

## Сім'я (Family Vocabulary)

Ukrainian has two words for family: **сім'я** and **родина**. Both are common, both are correct, and you will hear them interchangeably. A Grade 1 textbook poem by Марія Братко captures both:

> Поділюся з вами я: В мене дружна є сім'я.

Notice the apostrophe in **сім'я** — this is the same apostrophe you learned in Module 4. It separates the **м** from the **я**, keeping them as distinct sounds. **Дружна** (close-knit, friendly) is a word Ukrainians often use to describe their families.

Here are the core family members you need. Each noun has a grammatical gender — this matters for possessive pronouns later:

| Ukrainian | English | Gender |
|-----------|---------|--------|
| **мама** / **мати** | mother | f |
| **тато** / **батько** | father | m |
| **брат** | brother | m |
| **сестра** | sister | f |
| **син** | son | m |
| **дочка** / **донька** | daughter | f |

**Мама** is everyday speech; **мати** is formal or literary. **Тато** is everyday; **батько** is formal. The plural **батьки** (parents) is one of the first words where the plural meaning differs from the singular — it does not mean "fathers."

Extended family members: **бабуся** / **баба** (grandmother), **дідусь** / **дід** (grandfather), **тітка** (aunt), **дядько** (uncle). A cultural note: Ukrainian has no single word for "grandparents" — you always say **бабуся і дідусь**. Diminutive forms are very common in families: **татусь** (daddy), **матуся** (mommy), **бабця** (granny). The word **дідусь** is already a diminutive of **дід**. A Grade 2 textbook has a fun unscrambling exercise with family words: "маам, отат, дусьід, басябу" — can you figure them out? мама, тато, дідусь, бабуся.

<!-- INJECT_ACTIVITY: match-family-vocab -->

## У мене є (I have)

Ukrainian does not use a verb for "have." Instead, the construction is literally "At me there-is": **У мене є брат** — "I have a brother." This is completely different from English "I have," and it is one of the first structures that shows you how Ukrainian thinks differently.

For A1, you need only three forms:

| Ukrainian | English |
|-----------|---------|
| **У мене є** | I have |
| **У тебе є** | You have (informal) |
| **У вас є** | You have (formal) |

Examples with family: **У мене є сестра** (I have a sister). **У тебе є брат?** (Do you have a brother?). **У вас є діти?** (Do you have children?). Other pronoun forms like **у нього є** (he has) and **у неї є** (she has) appeared in the dialogues above as memorized phrases — the full genitive pronoun system comes in A2. For now, just recognize them when you hear them.

Questions use rising intonation only — no word-order change needed: **У тебе є сестра?** ↗ Compare English "Do you have...?" which requires a helper verb. Ukrainian is simpler here. Short answers: **Так, у мене є сестра.** Or simply: **Ні.** For now, avoid **У мене немає** (I don't have) — it requires the genitive case, which is A2 grammar. At A1, learners answer with: **Ні.** Or: **Ні, у мене тільки один брат.**

<!-- INJECT_ACTIVITY: quiz-u-tebe-ye -->

Numbers make a brief appearance here, because family talk naturally involves counting. Two numbers show gender agreement: **один брат** (one brother, masculine) vs. **одна сестра** (one sister, feminine). **Два брати** (two brothers, masculine) vs. **дві сестри** (two sisters, feminine). **Один/одна** and **два/дві** change by gender — this is your first encounter with number-gender agreement. Keep it to just these two numbers for now. Examples: **У мене є один брат і дві сестри.** **У мене є одна бабуся і два дідусі.**

:::tip Pattern Summary
Four sentences that show the full **У мене є** pattern in action:

1. **У мене є два брати.** *(I have two brothers.)*
2. **У тебе є сестра?** — **Так, у мене є одна сестра.** *(Do you have a sister? — Yes, I have one sister.)*
3. **У вас є діти?** — **Так, у мене є син і дочка.** *(Do you have children? — Yes, I have a son and a daughter.)*
4. **У мене є бабуся. Її звати Ганна.** *(I have a grandmother. Her name is Hanna.)*

Notice how **У мене є** connects naturally to family introductions from the dialogues.
:::

## Мій, моя, моє (Possessive Pronouns)

Possessives in Ukrainian match the gender of the **thing possessed**, not the owner. This is different from English "my," which never changes form.

| | Masculine | Feminine | Neuter | Plural |
|---|-----------|----------|--------|--------|
| my | **мій** | **моя** | **моє** | **мої** |

**Мій брат** (my brother — masculine noun). **Моя сестра** (my sister — feminine noun). **Моє місто** (my city — neuter noun). **Мої батьки** (my parents — plural noun). The key: look at the noun's gender, not who is speaking. A man says **моя сестра** (not *мій сестра) because **сестра** is feminine. A woman says **мій брат** because **брат** is masculine. The speaker's gender is irrelevant.

**Твій/твоя/твоє/твої** (your, informal) follows the same pattern: **твій тато** (your dad, masculine), **твоя мама** (your mom, feminine), **твоє ім'я** (your name, neuter), **твої друзі** (your friends, plural). Third-person possessives are even easier: **його** (his) and **її** (her) never change form regardless of the noun. **Його мама, його тато, його місто** — always **його**. **Її брат, її сестра, її місто** — always **її**. This makes **його** and **її** the simplest possessives in Ukrainian.

Let us revisit Dialogue 2 to see possessives at work: **Це моя мама. Це мій тато. Це моя сестра. Це мої брати.** The **Це** + possessive + noun pattern is the workhorse for family introductions. The full paradigm (**наш**, **ваш**, **їхній**) comes in A2 — at A1, **мій/твій/його/її** in the nominative case covers everything you need. A quick exchange shows the contrast between **мій** and **твій**:

> **Максим:** Це мій тато. *(This is my dad.)*
> **Оля:** А це твій брат? *(And is this your brother?)*

<!-- INJECT_ACTIVITY: fill-in-possessives -->

<!-- INJECT_ACTIVITY: fill-in-dialogue -->

## Підсумок — Summary

In this module you learned to talk about your family in Ukrainian. Three key patterns carry your family conversations: (1) **У мене є** + noun for saying what family you have, (2) **Це** + **мій/моя/моє** for introducing family members, and (3) **Як його/її звати?** for asking and giving names. You can now name **мама**, **тато**, **брат**, **сестра**, **бабуся**, **дідусь**, **дядько**, **тітка**, **син**, **дочка**, and **батьки**. You know that possessives change by gender — **мій брат** but **моя сестра** — and that **його** and **її** never change form.

Test yourself:

1. Name 5 family members in Ukrainian.
2. Say "I have a sister." — **У мене є сестра.**
3. What is the difference between **мій** and **моя**? (Gender of the noun!)
4. Introduce your family in 4–5 sentences using **Це мій/моя...** and **У мене є...**
5. Ask someone "Do you have a brother?" — **У тебе є брат?**

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
