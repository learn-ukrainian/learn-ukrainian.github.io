<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/verbs-group-two.yaml` file for module **17: Verbs Group II** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-conjugate -->`
- `<!-- INJECT_ACTIVITY: group-sort -->`
- `<!-- INJECT_ACTIVITY: quiz-correct-form -->`
- `<!-- INJECT_ACTIVITY: fill-in-sentences -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Conjugate: я говор__, ти говор__, він говор__'
  items: 10
  type: fill-in
- focus: Sort verbs into Group I (-ати) and Group II (-ити)
  items: 10
  type: group-sort
- focus: 'Choose correct form: Ти (бачу/бачиш/бачить) це?'
  items: 8
  type: quiz
- focus: 'Complete with correct verb form: Вона ___ українською. (говорити)'
  items: 6
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- дивитися (to watch — reflexive preview)
- вчитися (to learn — reflexive preview)
- любити (to love — review, Group II!)
- трохи (a little)
- добре (well)
- увечері (in the evening)
required:
- говорити (to speak)
- бачити (to see)
- робити (to do/make)
- вчити (to study/teach)
- просити (to ask/request)
- ходити (to go/walk regularly)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

Тарас and Микола run into each other at a мовне кафе — a language café where people practice Ukrainian over coffee. Тарас hears Микола ordering in Ukrainian and strikes up a conversation.

> **Тарас:** Привіт! Ти говориш українською? *(Hi! Do you speak Ukrainian?)*
> **Микола:** Так, я говорю трохи. А ти? *(Yes, I speak a little. And you?)*
> **Тарас:** Я бачу, що ти добре говориш! *(I see that you speak well!)*
> **Микола:** Дякую! Я вчу онлайн. *(Thanks! I study online.)*
> **Тарас:** Це нелегко, але цікаво. *(It's not easy, but interesting.)*
> **Микола:** Так! А де ти вчиш? *(Yes! And where do you study?)*
> **Тарас:** Я теж вчу онлайн. *(I also study online.)*
> **Микола:** Ми обидва говоримо українською! *(We both speak Ukrainian!)*

Look at the verbs Тарас and Микола used: **говориш** (you speak), **говорю** (I speak), **бачу** (I see), **вчу** (I study), **говоримо** (we speak). Every single one belongs to the same verb family — Group II. These verbs share a pattern in their endings that is different from Group I verbs like **читати** (to read) that you learned in the previous module.

Now a different scene — an evening at home. Оксана and Богдан are relaxing after a long day.

> **Оксана:** Що ти робиш увечері? *(What are you doing this evening?)*
> **Богдан:** Я дивлюся фільм. А ти? *(I'm watching a movie. And you?)*
> **Оксана:** Я вчу нові слова. *(I'm studying new words.)*
> **Богдан:** А потім? *(And then?)*
> **Оксана:** Потім дивлюся серіал. *(Then I watch a series.)*
> **Богдан:** Ти добре робиш! *(You're doing well!)*
> **Оксана:** Я прошу друга допомагати. *(I ask a friend to help.)*
> **Богдан:** Він говорить дуже добре. *(He speaks very well.)*

Notice **дивлюся** (I watch) — the **-ся** ending means "oneself." You will learn more about these reflexive verbs in Module 20. For now, just treat **дивлюся** as a single word meaning "I watch."

Three things to spot in both dialogues: first, every verb follows a recognizable pattern. Second, the **ти**-form always ends in **-иш** (говориш, робиш, вчиш). Third, the **він/вона** form ends in **-ить** (говорить). The next section explains exactly why.

## Друга дієвідміна (Group II Verbs)

Group II verbs have an infinitive ending in **-ити** (or **-іти**): **говорити** (to speak), **бачити** (to see), **робити** (to do/make), **вчити** (to study/teach), **просити** (to ask/request), **ходити** (to go/walk regularly). These are different from the Group I verbs you already know — verbs like **читати** (to read) and **слухати** (to listen) that end in **-ати**. The quickest test: check the **ти**-form. If it ends in **-иш** (like **говориш**, **бачиш**), it is Group II.

Here is the full conjugation of **говорити** — your master pattern for Group II:

| Особа (Person) | Однина (Singular) | Множина (Plural) |
|---|---|---|
| я / ми | говорю | говоримо |
| ти / ви | говориш | говорите |
| він, вона / вони | говорить | говорять |

Now the other five essential Group II verbs. Pay close attention to the **я**-form — it sometimes looks different:

- **бачити** (to see): бачу, бачиш, бачить, бачимо, бачите, **бачать**
- **робити** (to do): **роблю**, робиш, робить, робимо, робите, роблять
- **вчити** (to study): вчу, вчиш, вчить, вчимо, вчите, вчать
- **просити** (to request): **прошу**, просиш, просить, просимо, просите, просять
- **ходити** (to walk): **ходжу**, ходиш, ходить, ходимо, ходите, ходять

Why do some **я**-forms look unexpected? Group II has consonant changes — but only in the **я**-form. Here are the four key shifts:

- **б → бл**: робити → **роблю**
- **д → дж**: ходити → **ходжу**
- **с → ш**: просити → **прошу**
- **ч → ч** (no change): бачити → **бачу**

This is the most important thing to remember: these consonant changes happen ONLY in the **я**-form. Every other form — **ти**, **він/вона**, **ми**, **ви**, **вони** — follows the regular pattern perfectly. Practical tip: learn the **я**-form as a separate vocabulary item for each new verb. Once you know it, the rest is automatic.

As a warm-up before the activity: say the **я**, **ти**, and **він** forms of **вчити** and **ходити** out loud. Check your answers: вчу/вчиш/вчить and ходжу/ходиш/ходить.

<!-- INJECT_ACTIVITY: fill-in-conjugate -->

## Група I чи II? (Which Group?)

Now that you know both groups, here they are side by side. Compare **читати** (Group I) with **говорити** (Group II):

| Особа | читати (Group I) | говорити (Group II) |
|---|---|---|
| я | читаю | говорю |
| ти | читаєш | говориш |
| він/вона | читає | говорить |
| ми | читаємо | говоримо |
| ви | читаєте | говорите |
| вони | читають | говорять |

See the pattern? Group I endings carry the vowel **-є-** (чита**є**ш, чита**є**, чита**є**мо). Group II endings carry the vowel **-и-** (говор**и**ш, говор**и**ть, говор**и**мо). That single vowel is the difference between the two groups.

Two fast identification tests you can use with any verb:

1. **Check the ти-form:** Does it end in **-єш**? → Group I. Does it end in **-иш**? → Group II.
2. **Check the вони-form:** Does it end in **-ють**? → Group I. Does it end in **-ять** or **-ать**? → Group II.

Try it yourself: **бачиш** → ends in -иш → Group II. Confirmed: **бачать** (вони-form ends in -ать). **Читаєш** → ends in -єш → Group I. Confirmed: **читають** (вони-form ends in -ють).

Now an important detail about the **вони**-form in Group II. After sibilant consonants — **ч**, **ш**, **ж**, **щ** — the ending is **-ать**, not **-ять**:

- **бачать** (not ~~бачять~~) — because the stem ends in **ч**
- **кричать** (not ~~кричять~~) — same reason, stem ends in **ч**

After all other consonants, the **вони**-form takes **-ять**:

- **говорять**, **ходять**, **просять**

Ukrainian textbooks teach a useful trick (from Varzatska, Grade 4): put the verb in the **вони**-form. If it ends in **-ять** or **-ать** → Group II. If it ends in **-ють** or **-уть** → Group I. This one test works for every verb.

Here is a reality check: most high-frequency Ukrainian verbs are actually Group I. But the verbs you need most right now — **говорити**, **робити**, **бачити**, **ходити** — are all Group II. Mastering this group unlocks exactly the core everyday action verbs.

<!-- INJECT_ACTIVITY: group-sort -->

<!-- INJECT_ACTIVITY: quiz-correct-form -->

## Підсумок — Summary

Two verb groups, two ending patterns. Here is everything in one place:

**Group I** (infinitive in **-ати**): endings carry **-є-**
- -ю, -єш, -є, -ємо, -єте, -ють

**Group II** (infinitive in **-ити/-іти**): endings carry **-и-**
- -ю/-у, -иш, -ить, -имо, -ите, -ять/-ать

Consonant changes in Group II appear only in the **я**-form: **роблю** (б→бл), **ходжу** (д→дж), **прошу** (с→ш), **бачу** (ч stays ч). The sibilant rule: after **ч/ш/ж/щ**, the **вони**-form takes **-ать** (бачать, кричать). After everything else → **-ять** (говорять, ходять). The single most useful test: look at the **ти**-form — **-єш** means Group I, **-иш** means Group II.

Now go back and look at both dialogues with fresh eyes. Label every verb: **говориш** (II), **говорю** (II), **бачу** (II), **вчу** (II), **робиш** (II), **дивлюся** (II), **прошу** (II), **говорить** (II). Every single verb in today's dialogues was Group II. That is not a coincidence — these are among the highest-frequency action verbs in spoken Ukrainian. You have just learned the conjugation pattern for the verbs that carry most everyday conversation.

:::tip
**Самоперевірка (Self-check)**
:::

Test yourself on these five questions:

- Conjugate **бачити** for я, ти, він/вона → **бачу**, **бачиш**, **бачить** ✓
- Is **слухати** Group I or II? → Check the ти-form: **слухаєш** → -єш → Group I ✓
- Is **говорити** Group I or II? → Check the ти-form: **говориш** → -иш → Group II ✓
- What happens to **робити** in the я-form? → б→бл: **роблю** ✓
- Вони-form of **бачити** — -ять or -ать? → **бачать** (ч is a sibilant → -ать) ✓

If you got all five correct, you have a solid grasp of both conjugation groups. In the next module, you will learn the modal verbs **хотіти** (to want) and **могти** (to be able to) — verbs that let you express wishes and abilities.

<!-- INJECT_ACTIVITY: fill-in-sentences -->

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: verbs-group-two
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

**Level: A1.2-A1.3 (Module 17/55) — EARLY BEGINNER**

The learner knows the alphabet and ~200 words. They:
- Can read Ukrainian slowly
- Know basic nouns, adjectives, simple verb forms
- Cannot handle complex sentences or grammar terminology in Ukrainian

**Instructions in simple English with Ukrainian key terms in bold.**
Example: 'Choose the correct form of **мій/моя/моє**'

**Good activity types:** quiz, fill-in (simple sentences), match-up, group-sort, true-false, observe, anagram, translate (English→Ukrainian).


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-verbs-present
- **fill-in** — Відмінюй дієслово: Fill in correct verb conjugation for given person/number
  - Instruction: *Вставте правильну форму дієслова*
- **group-sort** — І чи ІІ дієвідміна?: Sort verbs by conjugation class (I vs II)
- **match-up** — Особа → форма: Match personal pronouns to verb conjugation forms
  - Instruction: *З'єднайте*
- **error-correction** — Виправ дієслово: Find incorrectly conjugated verb and fix it

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
