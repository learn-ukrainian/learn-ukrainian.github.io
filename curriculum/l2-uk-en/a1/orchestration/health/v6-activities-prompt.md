<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/health.yaml` file for module **53: Health** (a1).

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

- `<!-- INJECT_ACTIVITY: match-body-parts -->`
- `<!-- INJECT_ACTIVITY: fill-in-symptoms -->`
- `<!-- INJECT_ACTIVITY: fill-in-pharmacy -->`
- `<!-- INJECT_ACTIVITY: quiz-health-response -->`
- `<!-- INJECT_ACTIVITY: fill-in-pharmacy-doctor -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Match body parts to their English translations.
  items:
  - голова == head
  - живіт == stomach
  - горло == throat
  - спина == back
  - рука == hand/arm
  - нога == leg/foot
  - зуб == tooth
  - око == eye
  type: match-up
- focus: Complete the sentence with the correct symptom or body part.
  items:
  - У мене болить {голова|рука|нога}. Я хочу спати.
  - У мене болить {живіт|вухо|око}. Я не хочу їсти.
  - У мене болить {горло|спина|ніс} і є температура. Я не можу говорити.
  - У мене {кашель|нежить|зуб}, я постійно кашляю.
  - У мене болить {зуб|голова|нога}, мені потрібен стоматолог.
  - Я {хворий|лікар|аптека}. У мене болить голова і спина.
  type: fill-in
- focus: Choose the logical response to the health problem.
  items:
  - options:
    - Ось таблетки від головного болю.
    - Ось краплі від нежиті.
    - Випийте сироп від кашлю.
    question: У мене болить голова.
  - options:
    - Вам потрібні таблетки від кашлю.
    - Ось краплі для носа.
    - У мене болить зуб.
    question: У мене сильний кашель.
  - options:
    - У мене болить горло.
    - Я лікар.
    - Де аптека?
    question: Що у вас болить?
  - options:
    - Ось краплі, будь ласка.
    - У мене болить спина.
    - Це таблетки від головного болю.
    question: Добрий день. Дайте, будь ласка, щось від нежиті.
  type: quiz
- focus: At the pharmacy or doctor - using target chunks.
  items:
  - Дайте, {будь ласка|добрий день|дякую}, таблетки від головного болю.
  - Що у вас {болить|хворий|лікар}?
  - У мене {температура|аптека|лікар} і болить горло.
  - Мені {погано|хворий|добре}. Викличте лікаря!
  - Де тут найближча {аптека|голова|спина}? Мені потрібні ліки.
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- спина (back, f)
- око (eye, n)
- вухо (ear, n)
- зуб (tooth, m)
- ніс (nose, m)
- температура (fever/temperature, f)
- кашель (cough, m)
- нежить (runny nose, f)
- таблетка (pill, f)
- хворий (sick, adj)
required:
- голова (head, f)
- горло (throat, n)
- живіт (stomach, m)
- рука (hand/arm, f)
- нога (leg/foot, f)
- болить (hurts — chunk: у мене болить)
- лікар (doctor, m)
- аптека (pharmacy, f)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Dialogues

Оленка wakes up feeling terrible — her head is pounding and her throat is on fire. Time to visit the **лікар** (doctor).

> **Лікар:** Добрий день! Що у вас болить? *(Good day! What hurts?)*
> **Пацієнтка:** У мене болить голова і горло. *(My head and throat hurt.)*
> **Лікар:** Давно? *(For long?)*
> **Пацієнтка:** З учора. І в мене температура. *(Since yesterday. And I have a fever.)*
> **Лікар:** Ви кашляєте? *(Are you coughing?)*
> **Пацієнтка:** Так, трохи. І є нежить. *(Yes, a little. And I have a runny nose.)*
> **Лікар:** Зрозуміло. Це застуда. *(Understood. It's a cold.)*
> **Пацієнтка:** Що мені робити? *(What should I do?)*
> **Лікар:** Я випишу ліки. Відпочивайте! *(I'll prescribe medicine. Rest!)*
> **Пацієнтка:** Дякую, лікарю! *(Thank you, doctor!)*

With her prescription in hand, Оленка walks to the **аптека** (pharmacy) next door.

> **Оленка:** Добрий день! У мене болить голова. Дайте, будь ласка, таблетки. *(Good day! My head hurts. Give me pills, please.)*
> **Фармацевт:** Проти головного болю? *(For a headache?)*
> **Оленка:** Так. І проти кашлю, будь ласка. *(Yes. And for a cough, please.)*
> **Фармацевт:** Ось, будь ласка. Ще щось? *(Here you go. Anything else?)*
> **Оленка:** А є щось проти нежитю? *(Do you have something for a runny nose?)*
> **Фармацевт:** Так, ось краплі. *(Yes, here are drops.)*
> **Оленка:** Дякую! Скільки це коштує? *(Thanks! How much does this cost?)*
> **Фармацевт:** Сто двадцять гривень. *(One hundred twenty hryvnias.)*
> **Оленка:** Будь ласка. *(Here you go.)*

Notice three key chunks from these dialogues. First: **У мене болить...** (I have a pain in...) — the essential phrase for telling anyone what hurts. Second: **Дайте, будь ласка...** (Give me... please) — the polite request form you already know from shopping modules. Third: **проти головного болю** (for a headache), **проти кашлю** (for a cough), **проти нежитю** (for a runny nose) — these are how you ask for specific medicine. You don't need to analyse the grammar behind these yet — that comes at A2. For now, treat them as ready-made chunks.

## Тіло (The Body)

Here are the ten body parts you need at A1. Each one has a grammatical gender — this matters for adjective agreement, but right now your main job is simply learning the words:

- **голова** (head, f)
- **горло** (throat, n)
- **спина** (back, f)
- **живіт** (stomach, m)
- **рука** (hand/arm, f)
- **нога** (leg/foot, f)
- **око** (eye, n)
- **вухо** (ear, n)
- **зуб** (tooth, m)
- **ніс** (nose, m)

Two important notes: **рука** covers the entire arm including the hand — Ukrainian doesn't split them at A1. The same goes for **нога**, which means the whole leg including the foot. If you stub your toe or twist your ankle, it's still **нога**.

Why do genders matter here? Because adjectives must agree: **велике око** (big eye — neuter), **великий ніс** (big nose — masculine), **велика рука** (big hand — feminine). But at this stage, you'll mostly use these words in the chunk **У мене болить...**, where gender doesn't change anything. Memorise the words first — full adjective agreement practice comes at A2.

<!-- INJECT_ACTIVITY: match-body-parts -->

Imagine Михайлик is drawing a person and labelling the parts: «Ось **голова**!» *(Here's the head!)* He draws two arms: «А це **рука** і **рука**.» *(And this is an arm and an arm.)* Then the legs: «Це **нога**.» *(This is a leg.)* He adds a face: «Ось **ніс**, **око** і **вухо**.» *(Here's the nose, eye, and ear.)* He points to the middle: «А тут **живіт**!» *(And here's the stomach!)* Finally he writes across the back: «І **спина**!» *(And the back!)* Simple labelling like this — pointing and naming — is exactly how Ukrainian Grade 1 textbooks introduce body parts.

A few pronunciation tips for tricky words. **Горло** — the «г» is a voiced sound, softer than English "g." Think of a gentle vibration in the throat, not a hard stop. **Живіт** — the «ж» sounds like the "s" in English "measure" or "pleasure." **Вухо** starts with two distinct sounds: «в» then «у» — don't blend them into an English "w." When in doubt about stress or exact pronunciation, check the словник tab where every word has audio.

## У мене болить... (It Hurts...)

The single most useful health phrase in Ukrainian is **У мене болить** + a body part. Learn it as one chunk — a ready-made sentence starter. Here are the five core combinations:

1. **У мене болить голова.** (My head hurts.)
2. **У мене болить живіт.** (My stomach hurts.)
3. **У мене болить горло.** (My throat hurts.)
4. **У мене болить спина.** (My back hurts.)
5. **У мене болить зуб.** (My tooth hurts.)

The literal structure is "at me hurts head" — that's a dative construction, and you'll study it properly at A2. For now, just memorise the pattern: **У мене болить** + whatever hurts.

When more than one thing hurts — or when the body part is naturally plural — **болить** changes to **болять**:

- **У мене болять зуби.** (My teeth hurt.)
- **У мене болять ноги.** (My legs hurt.)
- **У мене болять очі.** (My eyes hurt.)

You don't need to produce these forms yet. Just recognise them when you hear a doctor or friend say **болять** — it means multiple things hurt.

<!-- INJECT_ACTIVITY: fill-in-symptoms -->

Beyond **болить**, there are several common symptom chunks. Each one is a complete statement you can use as-is:

- **У мене температура.** (I have a fever. — literally "I have temperature")
- **У мене кашель.** (I have a cough.)
- **У мене нежить.** (I have a runny nose.)
- **Мені холодно.** (I'm cold.)
- **Мені погано.** (I feel unwell.)
- **Я хворий.** (I'm sick. — if you're male)
- **Я хвора.** (I'm sick. — if you're female)

Notice that **У мене температура** doesn't use **болить** — the fever doesn't "hurt," it "is with you." And **Мені погано** uses **мені** (another dative form) — again, just learn it as a chunk for now.

At the doctor or pharmacy, combine these chunks naturally. A sick person might say: **У мене болить горло і є температура.** (My throat hurts and I have a fever.) Or: **Я хвора. У мене кашель і нежить.** (I'm sick. I have a cough and a runny nose.) You already have enough vocabulary to describe a full set of symptoms — real Ukrainian you'd use on day one in Kyiv.

<!-- INJECT_ACTIVITY: fill-in-pharmacy -->

## Summary

Here is your complete health toolkit from this module.

**Body parts:**
**голова**, **горло**, **живіт**, **спина**, **рука**, **нога**, **око**, **вухо**, **зуб**, **ніс**

**Symptom chunks:**
- **У мене болить** [body part].
- **У мене температура / кашель / нежить.**
- **Мені погано.**
- **Я хворий / хвора.**

Two real situations where you'll use all of this:

**At the doctor (у лікаря):**
- Doctor asks: **Що у вас болить?** → You answer: **У мене болить...**

**At the pharmacy (в аптеці):**
- **Дайте, будь ласка, таблетки проти головного болю.** (Give me pills for a headache, please.)
- **Дайте краплі проти нежитю.** (Give me drops for a runny nose.)
- **Дайте сироп проти кашлю.** (Give me syrup for a cough.)

<!-- INJECT_ACTIVITY: quiz-health-response -->

Test yourself with these three questions:

- How do you say "My throat hurts and I have a fever"? → **У мене болить горло і є температура.**
- You're at the pharmacy. You need something for a cough. What do you say? → **Дайте, будь ласка, щось проти кашлю.**
- How do you say "I feel unwell"? → **Мені погано.**

If you got all three, you're ready for real-world health situations.

Looking ahead: module 54 (Emergencies) builds directly on this vocabulary. You'll learn phrases like **виклик швидкої** (calling an ambulance), describe urgent situations, and use past-tense forms from module 52. The chunk **У мене болить...** will reappear constantly across future modules — it's one of those patterns that, once learned, never stops being useful.

<!-- INJECT_ACTIVITY: fill-in-pharmacy-doctor -->

## Підсумок

This module gave you the tools to talk about health in Ukrainian. You can now:

- ✅ Name ten body parts: **голова, горло, живіт, спина, рука, нога, око, вухо, зуб, ніс**
- ✅ Say what hurts: **У мене болить голова.**
- ✅ Describe symptoms: **У мене температура. У мене кашель. Мені погано.**
- ✅ Tell a doctor what's wrong: **У мене болить горло і є температура.**
- ✅ Ask for medicine at a pharmacy: **Дайте, будь ласка, таблетки проти головного болю.**
- ✅ Say you're sick: **Я хворий** (m) / **Я хвора** (f)

Remember: **У мене болить...** is a chunk. Don't try to analyse the grammar — just use it. The grammar explanation comes at A2. For now, you have everything you need to walk into a Ukrainian pharmacy or doctor's office and be understood.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: health
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

**Level: A1.4+ (Module 53/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


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
