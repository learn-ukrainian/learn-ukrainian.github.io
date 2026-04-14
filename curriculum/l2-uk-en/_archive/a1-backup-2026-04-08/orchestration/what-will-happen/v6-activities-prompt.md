<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/what-will-happen.yaml` file for module **50: What Will Happen?** (a1).

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

- `<!-- INJECT_ACTIVITY: match-buty-future-forms -->`
- `<!-- INJECT_ACTIVITY: fill-in-analytic-future -->`
- `<!-- INJECT_ACTIVITY: fill-in-tense-distinction -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Match pronoun to the correct form of 'бути' (future)
  pairs:
  - я: буду
  - ти: будеш
  - він/вона: буде
  - ми: будемо
  - ви: будете
  - вони: будуть
  type: matching
- focus: Complete the analytic future tense (бути + infinitive)
  items:
  - Завтра я {буду|буде|будемо} працювати.
  - Що ти {будеш|буду|будете} робити ввечері?
  - Вона {буде|будуть|будемо} читати книжку.
  - Ми {будемо|буде|буду} дивитися футбол.
  - Ви {будете|будеш|будуть} гуляти в парку?
  - Вони {будуть|будемо|буде} відпочивати.
  type: fill-in
- focus: Distinguish between past, present, and future tenses
  items:
  - Зараз я {читаю|читав|буду читати}.
  - Учора він {гуляв|гуляє|буде гуляти} у парку.
  - Завтра ми {будемо дивитися|дивилися|дивимося} фільм.
  - Минулого тижня вона {працювала|працює|буде працювати}.
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- відпочивати (to rest)
- наступний (next, adj)
- тиждень (week, m)
- план (plan, m)
- звучати (to sound)
- футбол (football, m)
- зараз (now)
required:
- завтра (tomorrow)
- буду (I will — form of бути)
- будеш (you will)
- буде (he/she/it will)
- будемо (we will)
- будете (you pl. will)
- будуть (they will)
- робити (to do)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Dialogues

A fair. Music. Bright lights. A woman in a shawl sits behind a crystal ball. She looks up at you and smiles.

> **Ворожка:** Ти будеш багато подорожувати. *(You will travel a lot.)*
> **Ворожка:** Будеш знаходити нових друзів. *(You will find new friends.)*
> **Ворожка:** Будеш отримувати подарунки. *(You will receive gifts.)*
> **Ворожка:** Будеш щаслива! *(You will be happy!)*
> **Клієнт:** Справді? А коли це буде? *(Really? And when will that be?)*
> **Ворожка:** Скоро! Твоє майбутнє — яскраве! *(Soon! Your future is bright!)*

The **ворожка** (fortune teller) keeps repeating one word: **будеш** — "you will." Every prediction follows the same pattern: **будеш** + infinitive. The infinitive is the base form of a verb — the "-ти" form you already know: **подорожувати** (to travel), **знаходити** (to find), **отримувати** (to receive). This is the Ukrainian future tense, and it is remarkably simple.

Now listen to two friends planning their week. Every form of **буду** appears in this conversation — count them.

> **Андрій:** Що ти будеш робити завтра? *(What will you do tomorrow?)*
> **Марина:** Завтра я буду працювати. *(Tomorrow I will work.)*
> **Андрій:** А ввечері? *(And in the evening?)*
> **Марина:** Ввечері я буду готувати вечерю. *(In the evening I will cook dinner.)*
> **Андрій:** А що буде робити Олена? *(And what will Olena do?)*
> **Марина:** Вона буде читати. *(She will read.)*
> **Андрій:** А ви будете гуляти? *(And will you [all] go for a walk?)*
> **Марина:** Так, ми будемо гуляти в парку! *(Yes, we will walk in the park!)*

*Every person of **буду** appears in this dialogue — **буду**, **будеш**, **буде**, **будемо**, **будете**. Did you catch them all?*

Here is another conversation — weekend plans between colleagues.

> **Оксана:** Що ви будете робити на вихідних? *(What will you do on the weekend?)*
> **Тарас:** У суботу ми будемо відпочивати. *(On Saturday we will rest.)*
> **Оксана:** А в неділю? *(And on Sunday?)*
> **Тарас:** У неділю я буду готувати. *(On Sunday I will cook.)*
> **Тарас:** А чоловік буде гуляти з дітьми. *(And my husband will walk with the kids.)*
> **Оксана:** Чудово! А я буду дивитися футбол. *(Wonderful! And I will watch football.)*
> **Тарас:** Ти завжди будеш дивитися футбол! *(You will always watch football!)*

*Notice **«Чудово!»** — a useful reaction meaning "Wonderful!" And the playful teasing at the end: **завжди будеш дивитися** — "you'll always watch."*

<!-- INJECT_ACTIVITY: match-buty-future-forms -->

## Майбутній час (Future Tense)

Ukrainian textbooks call this **майбутній час** (future tense). Ukrainian actually has two ways to form the future, but at A1 you only need one: the **складений майбутній** (analytic future). The pattern is straightforward — take the helper verb **буду** (conjugated for person) and add any infinitive after it. Think of it like English "will + verb": **Я буду читати** = "I will read." The infinitive **читати** never changes. Only **буду** shifts to match the subject.

Here is the full conjugation — six forms of **бути** (to be) in the future, each paired with the infinitive **читати** (to read):

| Person | Singular | Plural |
|--------|----------|--------|
| 1st | **я буду читати** | **ми будемо читати** |
| 2nd | **ти будеш читати** | **ви будете читати** |
| 3rd | **він / вона буде читати** | **вони будуть читати** |

The pattern is always the same: one of the six forms of **бути** + the infinitive. The infinitive stays identical every time — **читати**, **працювати**, **гуляти** — it does not matter which verb follows. Only **буду** carries the person information.

Now compare all three tenses you know, using the same verb **читати**:

- **Минулий** (past): **Я читав / читала книжку вчора.** *(I read a book yesterday.)* — The verb takes a gender ending, as you learned in M49.
- **Теперішній** (present): **Я читаю книжку зараз.** *(I am reading a book now.)* — The verb takes a person ending.
- **Майбутній** (future): **Я буду читати книжку завтра.** *(I will read a book tomorrow.)* — The helper **буду** carries person; the main verb stays as the infinitive.

Three tenses, three different strategies: past relies on gender, present on person endings, and future on the helper verb **буду** + infinitive.

:::note
You may hear forms like **читатиму** or **робитиму** — this is the synthetic future, another way to express the same meaning. It is natural and common, but it is A2 material. At A1, always use **буду + infinitive** — it works in every situation and is fully correct. The Litvinova Grade 7 textbook confirms both forms are equivalent.
:::

## Практика (Practice)

The beauty of the analytic future is its predictability. Take any verb you know, keep it in the infinitive, and put the right form of **буду** before it. Here are six core verbs — all six persons for each:

- **читати** (to read) → **буду читати, будеш читати, буде читати, будемо читати, будете читати, будуть читати**
- **працювати** (to work) → **буду працювати, будеш працювати, буде працювати, будемо працювати, будете працювати, будуть працювати**
- **готувати** (to cook) → **буду готувати, будеш готувати, буде готувати, будемо готувати, будете готувати, будуть готувати**
- **гуляти** (to walk) → **буду гуляти, будеш гуляти, буде гуляти, будемо гуляти, будете гуляти, будуть гуляти**
- **дивитися** (to watch) → **буду дивитися, будеш дивитися, буде дивитися, будемо дивитися, будете дивитися, будуть дивитися**
- **говорити** (to speak) → **буду говорити, будеш говорити, буде говорити, будемо говорити, будете говорити, будуть говорити**

The infinitive form stays identical regardless of which verb follows **буду**. The only thing you conjugate is **бути** itself.

<!-- INJECT_ACTIVITY: fill-in-analytic-future -->

Now build full sentences. Pay attention to the **time expressions** — they tell the listener *when* the action will happen:

- **Завтра** я буду працювати з дев'ятої до п'ятої. *(Tomorrow I will work from nine to five.)*
- **Ввечері** ми будемо дивитися фільм. *(In the evening we will watch a film.)*
- **У суботу** вони будуть гуляти в парку. *(On Saturday they will walk in the park.)*
- Що ви будете їсти **на вечерю**? *(What will you eat for dinner?)*
- **Наступного тижня** він буде відпочивати. *(Next week he will rest.)*
- **Вранці** вона буде готувати сніданок. *(In the morning she will cook breakfast.)*

:::tip
Key time words for the future: **завтра** (tomorrow), **ввечері** (in the evening), **вранці** (in the morning), **у суботу** (on Saturday), **наступного тижня** (next week).
:::

<!-- INJECT_ACTIVITY: fill-in-tense-distinction -->

## Summary

To form the analytic future in Ukrainian, take **буду** (conjugated for person) and add the infinitive of any verb. The infinitive never changes — regardless of gender, number, or person. There are six forms of **бути** in the future: **буду, будеш, буде, будемо, будете, будуть**. That is the entire system. Pick the right form of **бути**, add any infinitive, and you have the future tense.

Here are all three tenses side by side, using the same verb **читати**:

- **Учора я читав / читала.** → Минулий час (gender ending)
- **Зараз я читаю.** → Теперішній час (person ending)
- **Завтра я буду читати.** → Майбутній час (**буду** + infinitive)

You can now speak about yesterday, today, and tomorrow in Ukrainian.

The single most useful future-tense question at A1 is **«Що ти будеш робити?»** — "What will you do?" Memorise it as a chunk. Here are three model exchanges:

> **— Що ти будеш робити завтра?** *(What will you do tomorrow?)*
> **— Завтра я буду працювати.** *(Tomorrow I will work.)*

> **— Що вона буде робити ввечері?** *(What will she do in the evening?)*
> **— Вона буде читати книжку.** *(She will read a book.)*

> **— Що ви будете робити у суботу?** *(What will you do on Saturday?)*
> **— У суботу ми будемо відпочивати.** *(On Saturday we will rest.)*

## Підсумок

Check yourself — can you answer these without looking back?

- What is the analytic future? → **буду** + infinitive
- What changes in **«ми будемо читати»**? → Only **будемо** — the infinitive stays fixed
- How do you say "She will rest"? → **Вона буде відпочивати.**
- How do you say "They will cook"? → **Вони будуть готувати.**
- What is the future of **«Ти читаєш»**? → **Ти будеш читати.**
- How do you ask "What will you do tomorrow?" → **Що ти будеш робити завтра?**

If you answered all six, you have the Ukrainian future tense. In the next module, you will use it to talk about your own plans — **«Мої плани»**.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: what-will-happen
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

**Level: A1.4+ (Module 50/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


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
