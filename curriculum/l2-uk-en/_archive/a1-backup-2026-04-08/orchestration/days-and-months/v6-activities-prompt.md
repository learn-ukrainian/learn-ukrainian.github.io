<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/days-and-months.yaml` file for module **23: Days and Months** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-days-order -->`
- `<!-- INJECT_ACTIVITY: match-months-seasons -->`
- `<!-- INJECT_ACTIVITY: fill-in-chunks -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Put days of the week in order
  items:
  - понеділок, {вівторок|субота|четвер}, середа
  - середа, {четвер|п'ятниця|неділя}, п'ятниця
  - п'ятниця, {субота|вівторок|середа}, неділя
  - неділя, {понеділок|вівторок|четвер}, вівторок
  - вівторок, середа, {четвер|п'ятниця|неділя}
  - четвер, п'ятниця, {субота|понеділок|вівторок}
  - субота, {неділя|понеділок|п'ятниця}, понеділок
  type: fill-in
- focus: Match the month to the correct season
  pairs:
  - січень ↔ зима
  - квітень ↔ весна
  - липень ↔ літо
  - жовтень ↔ осінь
  - лютий ↔ зима
  - травень ↔ весна
  - серпень ↔ літо
  - листопад ↔ осінь
  type: match-up
- focus: Use the correct 'in/on' chunk for days and months
  items:
  - Я працюю {у понеділок|понеділок|в понеділок}.
  - Мій день народження {у березні|березень|в березень}.
  - Ми гуляємо {в суботу|субота|у субота}.
  - '{Взимку|Зима|У зима} холодно.'
  - Я вивчаю українську {у вівторок|вівторок|в вівторок}.
  - Вони відпочивають {у серпні|серпень|в серпень}.
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- січень, лютий, березень (Jan, Feb, Mar)
- квітень, травень, червень (Apr, May, Jun)
- липень, серпень, вересень (Jul, Aug, Sep)
- жовтень, листопад, грудень (Oct, Nov, Dec)
- день народження (birthday)
required:
- понеділок, вівторок, середа (Mon, Tue, Wed)
- четвер, п'ятниця (Thu, Fri)
- субота, неділя (Sat, Sun)
- тиждень (week, m)
- зима, весна, літо, осінь (winter, spring, summer, autumn)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалоги (Dialogues)

**Що ти робиш у понеділок?** Your friend wants to make plans for the week. How do you answer? You need the days of the week — and in Ukrainian, they carry stories inside their names. But first, listen to two conversations that show how Ukrainians talk about time.

**(Планування тижня / Planning the week)**

> **Тарас:** Що ти робиш у понеділок? *(What are you doing on Monday?)*
> **Оленка:** Я працюю. А у вівторок? *(I'm working. And on Tuesday?)*
> **Тарас:** У вівторок я вивчаю українську. *(On Tuesday I study Ukrainian.)*
> **Оленка:** А у суботу? *(And on Saturday?)*
> **Тарас:** У суботу гуляю з друзями. *(On Saturday I hang out with friends.)*
> **Оленка:** А в неділю? *(And on Sunday?)*
> **Тарас:** Неділя — вільний день! *(Sunday is a free day!)*

Tаras uses **у понеділок** (on Monday), **у вівторок** (on Tuesday), **у суботу** (on Saturday), and **в неділю** (on Sunday) to talk about his schedule. Each day pairs with **у** or **в** — a small word that means "on" when paired with a day. The endings of the days change slightly in these chunks: **субота** becomes **суботу**, **неділя** becomes **неділю**. For now, treat each "у/в + day" combination as a fixed phrase to memorize whole.

**(Коли у тебе день народження? / When is your birthday?)**

> **Марія:** Коли у тебе день народження? *(When is your birthday?)*
> **Андрій:** У березні. *(In March.)*
> **Марія:** Якого числа? *(What date?)*
> **Андрій:** П'ятнадцятого березня. А у тебе? *(The fifteenth of March. And yours?)*
> **Марія:** У мене в серпні. *(Mine is in August.)*
> **Андрій:** О, це літо! Тепло і сонячно. *(Oh, that's summer! Warm and sunny.)*

Here you see the same pattern with months: **у березні** (in March), **в серпні** (in August). The phrase **день народження** (birthday, literally "day of birth") is a fixed expression — memorize it as one unit. Андрій also connects the month to a season: **серпень** (August) belongs to **літо** (summer).

Notice how **у** or **в** keeps appearing before time words — **у понеділок**, **у вівторок**, **у березні**, **в серпні**. This is the core pattern of this module. Ukrainian uses **у/в** before days, months, and some seasons. You will see it again and again as we go deeper.

## Дні тижня (Days of the Week)

Ukrainian has seven days, and unlike English, they are always written in **lowercase** — no capital letters. English writes "Monday, Tuesday"; Ukrainian writes **понеділок, вівторок**. A capital letter appears only at the start of a sentence.

Here are all seven, starting from the beginning of the Ukrainian week:

- **понеділок** (Monday)
- **вівторок** (Tuesday)
- **середа** (Wednesday)
- **четвер** (Thursday)
- **п'ятниця** (Friday)
- **субота** (Saturday)
- **неділя** (Sunday)

Ukrainian calendars start the week on **понеділок**, not on Sunday as in some English-speaking countries. One important note: **неділя** means "Sunday," but the word for "week" is **тиждень**. In some dialects and older texts, **неділя** can mean "week," but in standard modern Ukrainian, a week is always a **тиждень**.

These names are not random sounds — they tell a story. **Четвер** comes from **четвертий** (fourth) — it is the fourth day. **П'ятниця** comes from **п'ять** (five) — the fifth day. **Середа** means "middle" — it sits in the middle of the working week. **Субота** has ancient roots shared with the word "Sabbath," borrowed long ago through Greek. Knowing these connections makes the days easier to remember: four, five, middle — **четвер, п'ятниця, середа**.

<!-- INJECT_ACTIVITY: fill-in-days-order -->

To say "on" a specific day, Ukrainian uses **у** or **в** followed by a special form of the day. Memorize each chunk as a whole phrase:

| Day | "On" that day |
|-----|---------------|
| понеділок | **у понеділок** |
| вівторок | **у вівторок** |
| середа | **у середу** |
| четвер | **у четвер** |
| п'ятниця | **у п'ятницю** |
| субота | **в суботу** |
| неділя | **в неділю** |

Some endings change: **середа** becomes **середу**, **п'ятниця** becomes **п'ятницю**, **субота** becomes **суботу**, **неділя** becomes **неділю**. Others stay the same: **понеділок, вівторок, четвер**. Do not try to figure out the grammar rule behind this yet — just memorize each chunk as a unit, the way a child learns "on Monday" without analyzing why "on" is there.

Here are four sentences showing these chunks in action:

- **Я навчаюся у вівторок і в четвер.** — I study on Tuesday and Thursday.
- **Тато працює у понеділок.** — Dad works on Monday.
- **У п'ятницю ми дивимося фільм.** — On Friday we watch a movie.
- **В суботу я сплю довго.** — On Saturday I sleep late.

## Місяці і пори року (Months and Seasons)

Ukrainian organizes the year into four seasons, and each season holds three months. The seasons are:

- **Зима** (winter) — сніг і холод (snow and cold)
- **Весна** (spring) — квіти і тепло (flowers and warmth)
- **Літо** (summer) — сонце і море (sun and sea)
- **Осінь** (autumn) — листя і дощ (leaves and rain)

Now the twelve months, grouped by season — all **lowercase**, just like days:

| Зима (winter) | Весна (spring) | Літо (summer) | Осінь (autumn) |
|---|---|---|---|
| **грудень** (Dec) | **березень** (Mar) | **червень** (Jun) | **вересень** (Sep) |
| **січень** (Jan) | **квітень** (Apr) | **липень** (Jul) | **жовтень** (Oct) |
| **лютий** (Feb) | **травень** (May) | **серпень** (Aug) | **листопад** (Nov) |

Ukrainian month names come from nature — not from Roman gods like "January" or "March" in English. **Березень** (March) comes from **береза** (birch tree) — birch sap flows in early spring. **Липень** (July) comes from **липа** (linden tree) — linden blossoms fill the air in July. **Листопад** (November) literally means "leaves fall" — **листя** (leaves) + **падати** (to fall). This is a Ukrainian linguistic fingerprint: the calendar is a nature calendar. All twelve months are masculine gender.

<!-- INJECT_ACTIVITY: match-months-seasons -->

To say "in" a specific month, Ukrainian uses **у/в** with a changed form of the month name. Here are all twelve:

- **у січні** (in January), **у лютому** (in February), **в березні** (in March)
- **у квітні** (in April), **у травні** (in May), **в червні** (in June)
- **в липні** (in July), **в серпні** (in August), **у вересні** (in September)
- **в жовтні** (in October), **в листопаді** (in November), **в грудні** (in December)

Notice that **лютий** becomes **у лютому** — it follows a different pattern from the other months because **лютий** is originally an adjective (meaning "fierce" — fierce frosts!), not a noun like the rest.

For seasons, Ukrainian uses special frozen forms that cannot be broken apart. Memorize these four chunks:

- **взимку** (in winter)
- **навесні** (in spring)
- **влітку** (in summer)
- **восени** (in autumn)

These are adverbs — single words, not "у + season." They look different from the season names, so just learn each one by heart.

Two model sentences putting this together:

- **Мій день народження в жовтні.** — My birthday is in October.
- **Влітку я їжджу на море.** — In summer I go to the sea.

And four more mixing months and seasons:

- **У грудні холодно — це зима.** — In December it's cold — it's winter.
- **Навесні квітнуть дерева.** — In spring, trees bloom.
- **В серпні ми відпочиваємо.** — In August we rest.
- **Восени починається школа.** — In autumn, school begins.

<!-- INJECT_ACTIVITY: fill-in-chunks -->

## Підсумок — Summary

You now have the full Ukrainian calendar at your fingertips. Here is everything organized for quick reference and self-testing.

**Дні тижня** (Days of the week):

- понеділок, вівторок, середа, четвер, п'ятниця, субота, неділя
- Chunks: **у понеділок, у вівторок, у середу, у четвер, у п'ятницю, в суботу, в неділю**

**Місяці** (Months):

- січень, лютий, березень, квітень, травень, червень, липень, серпень, вересень, жовтень, листопад, грудень
- Chunks: **у січні, у лютому, в березні, у квітні, у травні, в червні, в липні, в серпні, у вересні, в жовтні, в листопаді, в грудні**

**Пори року** (Seasons):

- зима, весна, літо, осінь
- Chunks: **взимку, навесні, влітку, восени**

Test yourself — answer these questions in Ukrainian:

- **Який сьогодні день?** — What day is today?
- **Який зараз місяць?** — What month is it now?
- **Яка зараз пора року?** — What season is it now?
- **Коли у тебе день народження?** — When is your birthday?
- **Що ти робиш у суботу?** — What do you do on Saturday?

Try answering out loud. Use the chunks you learned: **У мене день народження в ...** (My birthday is in ...), **У суботу я ...** (On Saturday I ...). The goal is not to construct these from grammar rules — the goal is to reach for the whole chunk automatically, just as a native speaker does.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: days-and-months
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

**Level: A1.4+ (Module 23/55) — BEGINNER**

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
