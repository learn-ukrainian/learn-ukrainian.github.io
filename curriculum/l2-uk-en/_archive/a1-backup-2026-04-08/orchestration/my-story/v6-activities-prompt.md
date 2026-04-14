<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/my-story.yaml` file for module **52: My Story** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-signal-words -->`
- `<!-- INJECT_ACTIVITY: ordering-life-events -->`
- `<!-- INJECT_ACTIVITY: fill-in-biography -->`
- `<!-- INJECT_ACTIVITY: matching-verb-tense -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Put the life events in logical chronological order
  items:
  - Я народився в Торонто.
  - У дитинстві я жив з батьками.
  - Потім я вчився в університеті.
  - Зараз я живу в Києві і працюю програмістом.
  - Далі я буду подорожувати.
  type: ordering
- focus: Use signal words to determine the correct tense
  items:
  - Раніше я {жив|живу|буду жити} в Канаді.
  - Зараз я {працюю|працював|буду працювати} в університеті.
  - Далі я {буду вивчати|вивчав|вивчаю} українську мову.
  - У дитинстві вона {любила|любить|буде любити} читати.
  - Сьогодні ми {живемо|жили|будемо жити} в Україні.
  type: fill-in
- focus: Match the life event verb to the correct tense category
  pairs:
  - народився: Минулий час (Past)
  - переїхала: Минулий час (Past)
  - живу: Теперішній час (Present)
  - працюю: Теперішній час (Present)
  - буду подорожувати: Майбутній час (Future)
  - будемо вчитися: Майбутній час (Future)
  type: matching
- focus: Complete a biography combining all three tenses
  items:
  - Я {народилася|народився|народилися} у Львові.
  - Там я {вчилася|вчився|вчилися} в школі.
  - Зараз я {працюю|працювала|буду працювати} вчителькою.
  - Наступного року я {буду подорожувати|подорожувала|подорожую}.
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- подорожувати (to travel)
- закінчити (to finish/graduate)
- дитинство (childhood, n)
- університет (university, m)
- програміст (programmer, m)
- успіх (success, m)
- мрія (dream, f)
- батьки (parents, pl)
required:
- народитися (to be born)
- жити (to live)
- вчитися (to study)
- переїхати (to move)
- зараз (now)
- раніше (before/earlier)
- далі (further/next)
- розповідати (to tell/narrate)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Dialogues

Two people meet at a language school in Kyiv. One has lived here for years; the other just arrived. They want to know each other's full story — where they come from, what they do now, and what comes next.

> **Оксана:** Розкажи про себе! *(Tell me about yourself!)*
> **Максим:** Я народився в Канаді, у Торонто. *(I was born in Canada, in Toronto.)*
> **Оксана:** А зараз ти живеш тут? *(And now you live here?)*
> **Максим:** Так, зараз я живу в Києві. *(Yes, now I live in Kyiv.)*
> **Оксана:** Чому ти переїхав? *(Why did you move?)*
> **Максим:** Я хотів вивчати українську. *(I wanted to study Ukrainian.)* Мої бабуся і дідусь з України. *(My grandma and grandpa are from Ukraine.)*
> **Оксана:** А що ти будеш робити далі? *(And what will you do next?)*
> **Максим:** Я буду працювати тут і вчити мову. *(I will work here and learn the language.)*
> **Оксана:** Чудово! Успіхів тобі! *(Wonderful! Best of luck!)*

All three tenses appear in this single conversation. **Народився** (was born) — past. **Живу** (live) — present. **Буду працювати** (will work) — future. Maksym moves naturally from his childhood in Canada, through his present life in Kyiv, to his future plans. That is the shape of every life story.

Now hear Anna tell her story — from birth to future dreams.

> **Анна:** Я народилася у Львові. *(I was born in Lviv.)* Там я вчилася в школі. *(I studied at school there.)*
> **Колега:** А потім? *(And then?)*
> **Анна:** Потім я переїхала в Київ. *(Then I moved to Kyiv.)* Я закінчила університет. *(I finished university.)*
> **Колега:** А зараз? *(And now?)*
> **Анна:** Зараз я працюю вчителькою. *(Now I work as a teacher.)* Я живу в центрі міста. *(I live in the city centre.)*
> **Колега:** А що далі? *(And what's next?)*
> **Анна:** Я буду подорожувати! *(I will travel!)* Я хочу побачити Японію. *(I want to see Japan.)*
> **Колега:** І ти будеш вчити японську? *(And you'll learn Japanese?)*
> **Анна:** Може! Але спочатку — українська для тебе! *(Maybe! But first — Ukrainian for you!)*

Notice how Anna's story flows: past (**народилася**, **вчилася**, **переїхала**, **закінчила**) → present (**працюю**, **живу**) → future (**буду подорожувати**). The story moves forward in time, just like Maksym's. Past events first, then what is true now, then dreams. That is the shape of every life story in Ukrainian.

## Три часи разом (Three Tenses Together)

Every life story has three parts. Here is the scaffold you need:

**МИНУЛИЙ ЧАС** (past tense) — things that already happened:
- **Я народився** / **народилася** в... *(I was born in...)*
- **Я жив** / **жила** в... *(I lived in...)*
- **Я вчився** / **вчилася**... *(I studied...)*
- **Я працював** / **працювала**... *(I worked...)*

**ТЕПЕРІШНІЙ ЧАС** (present tense) — what is true right now:
- **Зараз я живу** в... *(Now I live in...)*
- **Я працюю**... *(I work...)*
- **Я вивчаю**... *(I study/am learning...)*
- **Я люблю**... *(I love...)*

**МАЙБУТНІЙ ЧАС** (future tense) — what will come:
- **Я буду працювати**... *(I will work...)*
- **Я буду вивчати**... *(I will study...)*
- **Я буду жити**... *(I will live...)*

Look at the past tense forms closely. Gender matters: **-в** for masculine (**я народивСЯ**) and **-ла** for feminine (**я народиЛАся**). Three more pairs: **жив** / **жила**, **вчився** / **вчилася**, **працював** / **працювала**. A man says **я народився**, a woman says **я народилася** — the ending always tells you.

Signal words are the listener's roadmap. They tell the listener which tense is coming before the verb arrives:

**Past signals:** **раніше** (before/earlier), **у дитинстві** (in childhood), **тоді** (back then).
**Present signals:** **зараз** (now), **сьогодні** (today), **цього року** (this year).
**Future signals:** **потім** (then/later), **далі** (further/next), **наступного року** (next year), **скоро** (soon).

Compare this pair: **Раніше я жив у Канаді** *(Before, I lived in Canada)* vs. **Зараз я живу в Україні** *(Now I live in Ukraine)*. Same verb root **жи-**, opposite tense, different signal word. The signal word does the work.

Ukrainian speakers use **А потім...** *(And then...)* to move from past to present and **А далі...** *(And next...)* to move from present to future. These two phrases are the hinges of every life story. Try it: **Я народився в Одесі. А потім я переїхав у Київ. А далі — я буду подорожувати!** *(I was born in Odesa. And then I moved to Kyiv. And next — I will travel!)*

<!-- INJECT_ACTIVITY: fill-in-signal-words -->

## Моя історія (My Story)

Now read a full model story. Taras is a programmer from Odesa who moved to Kyiv. Read his story and notice how all three tenses flow together naturally.

:::note
**Тарас розповідає** *(Taras tells his story)*

**Я народився в Одесі.** *(I was born in Odesa.)* **Я жив там з батьками і сестрою.** *(I lived there with my parents and sister.)* **У дитинстві я ходив у школу.** *(In childhood I went to school.)* **Я любив математику.** *(I loved maths.)* **Потім я переїхав у Київ.** *(Then I moved to Kyiv.)* **Я вчився в університеті.** *(I studied at university.)*

**Зараз я живу в Києві.** *(Now I live in Kyiv.)* **Я працюю програмістом.** *(I work as a programmer.)* **Я люблю свою роботу.** *(I love my job.)* **На дозвіллі я граю у футбол.** *(In my free time I play football.)* **Я читаю книжки.** *(I read books.)*

**Далі я буду подорожувати.** *(Next I will travel.)* **Я буду вивчати англійську.** *(I will study English.)* **І я буду жити в Києві.** *(And I will live in Kyiv.)* **Це моє місто!** *(This is my city!)*
:::

The tense shifts are clear. Past verbs: **народився**, **жив**, **ходив**, **любив**, **переїхав**, **вчився**. Present verbs: **живу**, **працюю**, **люблю**, **граю**, **читаю**. Future constructions: **буду подорожувати**, **буду вивчати**, **буду жити**. Each block has its own signal word: **у дитинстві** and **потім** for the past, **зараз** for the present, **далі** for the future.

<!-- INJECT_ACTIVITY: ordering-life-events -->

Now your turn. Tell YOUR story using the same scaffold:

**Past** — start with: **Я народився** / **народилася** в [місто/країна]. Then add: **Я жив/жила...** **Я вчився/вчилася...** Use at least three past verbs with the correct gender ending (**-в** or **-ла**).

**Present** — shift with **зараз**: **Зараз я живу...** **Я працюю...** **Я вивчаю українську.** Why are you learning? **Я вивчаю українську, тому що...** *(I'm studying Ukrainian because...)*

**Future** — shift with **далі**: **Я буду...** **Я хочу...** Use at least three **буду** + infinitive constructions.

Target: 8–10 sentences. Use **раніше** / **зараз** / **далі** to signal each tense shift.

<!-- INJECT_ACTIVITY: fill-in-biography -->

## Summary

Three tenses — three patterns. Here they are side by side.

**Минулий час** (past tense) — add **-в** (masculine), **-ла** (feminine), **-ло** (neuter), or **-ли** (plural) to the verb stem:
- **народи-в** / **народи-ла** *(was born)*
- **жи-в** / **жи-ла** *(lived)*
- **вчи-в-ся** / **вчи-ла-ся** *(studied)*

**Теперішній час** (present tense) — person endings:
- **я живу**, **ти живеш**, **він/вона живе**
- **ми живемо**, **ви живете**, **вони живуть**

**Майбутній час** (future tense) — **буду** + infinitive:
- **я буду подорожувати** *(I will travel)*
- **ти будеш працювати** *(you will work)*
- **він/вона буде вивчати** *(he/she will study)*

At A1, future tense always uses **буду** + infinitive — never a single conjugated form.

**Signal words — quick reference:**

**МИНУЛИЙ:** **раніше** *(earlier)*, **у дитинстві** *(in childhood)*, **тоді** *(back then)*, **потім** *(then, narrating past sequence)*.
**ТЕПЕРІШНІЙ:** **зараз** *(now)*, **сьогодні** *(today)*, **цього року** *(this year)*.
**МАЙБУТНІЙ:** **далі** *(next)*, **потім** *(then, pointing forward)*, **наступного року** *(next year)*, **скоро** *(soon)*.

:::tip
The word **потім** can signal a past sequence OR a future plan — context tells you which!
:::

**Life story vocabulary** — words every story needs:

- **народитися** *(to be born)* — я народився / народилася
- **жити** *(to live)* — я жив / жила / живу / буду жити
- **вчитися** *(to study)* — я вчився / вчилася / буду вчитися
- **переїхати** *(to move/relocate)* — я переїхав / переїхала
- **подорожувати** *(to travel)* — я буду подорожувати
- **закінчити** *(to finish/graduate)* — я закінчив / закінчила
- **розповідати** *(to tell/narrate)* — я розповідаю / буду розповідати

<!-- INJECT_ACTIVITY: matching-verb-tense -->

## Підсумок

Check yourself against these five questions:

- Can you say where you were born? (**Я народився/народилася в...**)
- Can you describe where you live NOW? (**Зараз я живу в...**)
- Can you say THREE things you did in the past? (use **-в/-ла** forms)
- Can you say TWO things you plan to do? (use **буду** + infinitive)
- Can you tell your whole story in 8 sentences, using signal words **раніше** / **зараз** / **далі**?

If you answered yes to all five — you can tell your life story in Ukrainian. **Я народився, я живу, я буду...** — your story has all three tenses. **Успіхів!** *(Best of luck!)*

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: my-story
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

**Level: A1.4+ (Module 52/55) — BEGINNER**

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
